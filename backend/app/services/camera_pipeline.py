"""
Camera scan pipeline — person detection, dirty detection, status automation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.core import camera_utils, yolo_models
from app.core.ids import new_id
from app.models import CleaningEvent, DiningSession, Table
from app.services import ai_service
from app.services.table_service import record_history
from app.socket_manager import socket_manager, sio

logger = logging.getLogger(__name__)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _reset_scan_counters(table: Table) -> None:
    table.consecutive_person_scans = 0
    table.consecutive_empty_scans = 0


def _effective_camera_url(table: Table) -> str | None:
    return table.camera_url or settings.default_camera_url


async def _emit(floor_id: str, event: str, data: object) -> None:
    await socket_manager.broadcast(floor_id, event, data)


async def _emit_table_update(_db: Session, table: Table) -> None:
    await sio.emit(
        "table_updated",
        {
            "id": table.id,
            "status": table.status,
            "floor_id": table.floor_id,
            "number": table.number,
        },
        room=str(table.floor_id),
    )


async def _auto_seat(db: Session, table: Table) -> None:
    now = datetime.now(timezone.utc)
    old_status = table.status
    session = DiningSession(
        id=new_id(),
        table_id=table.id,
        guest_name="Camera detected",
        party_size=2,
        seated_at=now,
        status="SEATED",
        host_id=None,
    )
    table.status = "SEATED"
    _reset_scan_counters(table)
    db.add(session)
    record_history(db, table.id, old_status, "SEATED", None, session.id)
    db.commit()
    db.refresh(table)
    db.refresh(session)

    from app.services.session_service import session_to_out

    await _emit_table_update(db, table)
    await _emit(
        table.floor_id,
        "session:created",
        session_to_out(session).model_dump(by_alias=True),
    )
    alert = ai_service.create_alert(
        db,
        event_type="SEATING_SUGGESTION",
        message=f"Guests detected at table {table.number} — auto-seated by camera",
        table_id=table.id,
        target_role="HOST",
    )
    await _emit(table.floor_id, "ai_alert", alert.model_dump(by_alias=True))


async def _handle_available(db: Session, table: Table, cropped) -> None:
    if yolo_models.person_model is None:
        return
    results = yolo_models.person_model(cropped, verbose=False)
    persons = yolo_models.count_persons(results)
    required = settings.consecutive_scans_required

    if persons > 0:
        table.consecutive_person_scans += 1
        if table.consecutive_person_scans >= required:
            await _auto_seat(db, table)
            return
    else:
        table.consecutive_person_scans = 0

    db.commit()


async def _handle_billing(db: Session, table: Table, cropped) -> None:
    if yolo_models.person_model is None:
        return
    results = yolo_models.person_model(cropped, verbose=False)
    persons = yolo_models.count_persons(results)
    required = settings.consecutive_scans_required

    if persons == 0:
        table.consecutive_empty_scans += 1
        if table.consecutive_empty_scans >= required:
            alert = ai_service.create_alert(
                db,
                event_type="DEPARTURE_ALERT",
                message=(
                    f"Table {table.number} — guests may have left "
                    f"({required} empty scans). Confirm payment before releasing."
                ),
                table_id=table.id,
                target_role="MANAGER",
            )
            await _emit(table.floor_id, "ai_alert", alert.model_dump(by_alias=True))
            table.consecutive_empty_scans = 0
    else:
        table.consecutive_empty_scans = 0

    db.commit()


async def _advance_clean_to_available(db: Session, table: Table, confidence: float) -> None:
    old = table.status
    table.status = "AVAILABLE"
    table.cleaning_started_at = None
    _reset_scan_counters(table)

    cleaning = (
        db.query(CleaningEvent)
        .filter(CleaningEvent.table_id == table.id, CleaningEvent.status != "COMPLETED")
        .order_by(CleaningEvent.requested_at.desc())
        .first()
    )
    if cleaning:
        now = datetime.now(timezone.utc)
        cleaning.status = "COMPLETED"
        cleaning.verified_by_ai = True
        cleaning.ai_confidence = confidence
        cleaning.completed_at = now
        if cleaning.requested_at:
            cleaning.duration_seconds = int((now - cleaning.requested_at).total_seconds())

    record_history(db, table.id, old, "AVAILABLE", None)
    db.commit()
    db.refresh(table)
    await _emit_table_update(db, table)


async def _handle_cleaning(db: Session, table: Table, cropped) -> None:
    started = _parse_iso(table.cleaning_started_at)
    if started:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed < settings.camera_cleaning_grace_seconds:
            return

    if yolo_models.dirty_model is None:
        return

    results = yolo_models.dirty_model(cropped, verbose=False)
    dirty_score = yolo_models.compute_dirty_score(results)

    if dirty_score == 0:
        await _advance_clean_to_available(db, table, 1.0 - dirty_score)
        return

    db.commit()

    if started:
        minutes = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if minutes >= 10:
            existing = (
                db.query(CleaningEvent)
                .filter(CleaningEvent.table_id == table.id)
                .order_by(CleaningEvent.requested_at.desc())
                .first()
            )
            if existing and existing.alert_fired_at is None:
                now = datetime.now(timezone.utc)
                existing.alert_fired_at = now
                alert = ai_service.create_alert(
                    db,
                    event_type="DIRTY_ALERT",
                    message=f"Table {table.number} still dirty after {int(minutes)} minutes",
                    table_id=table.id,
                    target_role="WAITER",
                )
                await _emit(table.floor_id, "ai_alert", alert.model_dump(by_alias=True))
            elif existing and existing.escalated_at is None and minutes >= 20:
                existing.escalated_at = datetime.now(timezone.utc)
                alert = ai_service.create_alert(
                    db,
                    event_type="DIRTY_ALERT",
                    message=f"Table {table.number} dirty 20+ min — manager attention needed",
                    table_id=table.id,
                    target_role="MANAGER",
                )
                await _emit(table.floor_id, "ai_alert", alert.model_dump(by_alias=True))
        db.commit()


async def process_table_scan(db: Session, table: Table, frame) -> None:
    roi = camera_utils.parse_roi(table.roi_coords)
    if not roi:
        return
    cropped = camera_utils.crop_roi(frame, roi)
    if cropped is None or cropped.size == 0:
        return

    status = table.status
    if status == "AVAILABLE":
        await _handle_available(db, table, cropped)
    elif status == "BILLING":
        await _handle_billing(db, table, cropped)
    elif status == "CLEANING":
        await _handle_cleaning(db, table, cropped)


def build_annotated_frame(db: Session, frame, tables: list[Table]):
    """Draw per-table overlays for the live stream demo."""
    from app.core import yolo_models

    annotated = frame.copy()
    now = datetime.now(timezone.utc)

    for table in tables:
        roi = camera_utils.parse_roi(table.roi_coords)
        if not roi:
            continue

        dirty = False
        sub_label = None

        if table.status == "CLEANING" and yolo_models.dirty_model is not None:
            started = _parse_iso(table.cleaning_started_at)
            if started:
                mins = int((now - started).total_seconds() / 60)
                sub_label = f"{mins} min"
            cropped = camera_utils.crop_roi(frame, roi)
            if cropped is not None and cropped.size > 0:
                results = yolo_models.dirty_model(cropped, verbose=False)
                dirty = yolo_models.compute_dirty_score(results) > 0

        color = camera_utils.STATUS_COLORS.get(table.status, (200, 200, 200))
        label = camera_utils.status_label(table.status, dirty=dirty)
        camera_utils.draw_table_overlay(
            annotated, roi, table.number, label, color, sub_label=sub_label
        )

    return annotated


async def run_scan_cycle(db: Session) -> None:
    """One 30-second scan pass across all configured tables."""
    tables = db.query(Table).all()
    if not tables:
        return

    by_camera: dict[str, list[Table]] = {}
    for table in tables:
        url = _effective_camera_url(table)
        if not url:
            continue
        by_camera.setdefault(url, []).append(table)

    for camera_url, cam_tables in by_camera.items():
        frame = await asyncio.to_thread(camera_utils.capture_frame, camera_url)
        if frame is None:
            continue

        annotated = build_annotated_frame(db, frame, cam_tables)
        camera_utils.set_stream_frame(annotated)

        for table in cam_tables:
            db.refresh(table)
            await process_table_scan(db, table, frame)
