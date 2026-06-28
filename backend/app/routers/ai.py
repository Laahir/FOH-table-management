from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_manager_or_owner
from app.database import get_db
from app.models import DiningSession, Table
from app.models.user import User
from app.schemas.ai import (
    AIEventCreate,
    AIEventOut,
    SeatingResponseOut,
    SeatingSuggestIn,
    ShiftReportOut,
)
from app.services import ai_service, ollama_service
from app.socket_manager import sio

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/events", response_model=list[AIEventOut])
def get_events(
    resolved: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AIEventOut]:
    return ai_service.list_alerts(db, resolved=resolved, user_role=current_user.role)


@router.post("/events", response_model=AIEventOut)
def create_event(
    body: AIEventCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_manager_or_owner),
) -> AIEventOut:
    alert = ai_service.create_alert(
        db,
        event_type=body.event_type,
        message=body.message,
        table_id=body.table_id,
        target_role=body.target_role,
    )
    floor_id = "floor-1"
    if body.table_id:
        table = db.get(Table, body.table_id)
        if table:
            floor_id = table.floor_id
    sio.emit_sync("ai_alert", alert.model_dump(by_alias=True), room=str(floor_id))
    return alert


@router.patch("/events/{event_id}/resolve")
def resolve_event(
    event_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, str | bool]:
    return ai_service.resolve_alert(db, event_id)


@router.post("/seating-suggest", response_model=SeatingResponseOut)
def seating_suggest(
    body: SeatingSuggestIn,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SeatingResponseOut:
    tables = (
        db.query(Table)
        .filter(Table.status.in_(("AVAILABLE", "RESERVED")))
        .all()
    )
    candidates = [
        {
            "id": t.id,
            "number": t.number,
            "capacity": t.capacity,
            "status": t.status,
            "section": t.section_id,
        }
        for t in tables
        if t.capacity >= body.party_size
    ]
    suggestion = ollama_service.seating_suggestion(body.party_size, candidates)
    return SeatingResponseOut(suggestion=suggestion, party_size=body.party_size)


@router.get("/reports/shift", response_model=ShiftReportOut)
def shift_report(
    report_date: str | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_manager_or_owner),
) -> ShiftReportOut:
    day = report_date or date.today().isoformat()
    sessions = db.query(DiningSession).all()
    today_sessions = [
        s for s in sessions
        if s.seated_at and s.seated_at.date().isoformat() == day
    ]
    stats = {
        "total_sessions": len(today_sessions),
        "tables_used": len({s.table_id for s in today_sessions}),
        "active_now": db.query(Table).filter(Table.status.in_(("SEATED", "ACTIVE", "BILLING"))).count(),
        "cleaning": db.query(Table).filter(Table.status == "CLEANING").count(),
    }
    content = ollama_service.shift_report(stats)
    return ShiftReportOut(report_date=day, content=content, stats=stats)
