from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.core.status_machine import ACTIVE_SESSION_STATUSES, is_valid_transition
from app.models import DiningSession, StatusHistory, Table
from app.schemas.floor import CreateTableIn, TableOut, TablePatchIn
from app.services.floor_service import get_current_floor, _table_to_out


def get_table(db: Session, table_id: str) -> Table:
    table = db.get(Table, table_id)
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return table


def active_session_for_table(db: Session, table_id: str) -> DiningSession | None:
    return (
        db.query(DiningSession)
        .filter(
            DiningSession.table_id == table_id,
            DiningSession.status.in_(ACTIVE_SESSION_STATUSES),
        )
        .first()
    )


def record_history(
    db: Session,
    table_id: str,
    from_status: str | None,
    to_status: str,
    user_id: str | None,
    session_id: str | None = None,
) -> None:
    db.add(
        StatusHistory(
            id=new_id(),  # uuid4 — no millisecond collision risk
            table_id=table_id,
            session_id=session_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=user_id,
            changed_at=datetime.now(timezone.utc),
        )
    )


def update_table(db: Session, table_id: str, patch: TablePatchIn) -> TableOut:
    table = get_table(db, table_id)
    data = patch.model_dump(exclude_unset=True, by_alias=False)
    for key, val in data.items():
        setattr(table, key, val)
    db.commit()
    db.refresh(table)
    return _table_to_out(table)


def patch_table_status(
    db: Session, table_id: str, new_status: str, user_id: str | None
) -> TableOut:
    table = get_table(db, table_id)
    if not is_valid_transition(table.status, new_status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid transition from {table.status} to {new_status}",
        )
    session = active_session_for_table(db, table_id)
    if new_status == "SEATED" and session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Table already has an active session",
        )
    old = table.status
    table.status = new_status
    if session:
        session.status = new_status
    record_history(db, table_id, old, new_status, user_id, session.id if session else None)
    db.commit()
    db.refresh(table)
    return _table_to_out(table)


def add_table(db: Session, payload: CreateTableIn) -> TableOut:
    floor = get_current_floor(db)
    w = payload.width if payload.width is not None else (64 if payload.shape == "CIRCLE" else 88)
    h = payload.height if payload.height is not None else (64 if payload.shape == "CIRCLE" else 72)
    table = Table(
        id=new_id(),  # uuid4
        floor_id=floor.id,
        section_id=payload.section_id,
        number=payload.number,
        capacity=payload.capacity,
        type=payload.type,
        shape=payload.shape,
        status="AVAILABLE",
        x=payload.x if payload.x is not None else 200,
        y=payload.y if payload.y is not None else 200,
        width=w,
        height=h,
        rotation=0,
    )
    db.add(table)
    db.commit()
    db.refresh(table)
    return _table_to_out(table)


def delete_table(db: Session, table_id: str) -> None:
    if active_session_for_table(db, table_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove table with an active session. Release the table first.",
        )
    table = get_table(db, table_id)
    db.query(DiningSession).filter(DiningSession.table_id == table_id).delete()
    db.delete(table)
    db.commit()
