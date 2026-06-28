from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.models import AIEvent
from app.schemas.ai import AIEventOut


ROLE_FILTER: dict[str, list[str]] = {
    "WAITER": ["WAIT_ALERT", "DIRTY_ALERT"],
    "HOST": ["WAIT_ALERT", "SEATING_SUGGESTION"],
    "MANAGER": [
        "WAIT_ALERT",
        "DIRTY_ALERT",
        "DEPARTURE_ALERT",
        "SEATING_SUGGESTION",
        "SHIFT_REPORT",
    ],
    "OWNER": [
        "WAIT_ALERT",
        "DIRTY_ALERT",
        "DEPARTURE_ALERT",
        "SEATING_SUGGESTION",
        "SHIFT_REPORT",
    ],
}


def ai_event_to_out(event: AIEvent) -> AIEventOut:
    created = event.created_at
    if created.tzinfo is None:
        created_str = created.isoformat() + "Z"
    else:
        created_str = created.isoformat().replace("+00:00", "Z")
    return AIEventOut(
        id=event.id,
        table_id=event.table_id,
        event_type=event.event_type,
        message=event.message,
        target_role=event.target_role,
        resolved=event.resolved,
        created_at=created_str,
    )


def create_alert(
    db: Session,
    *,
    event_type: str,
    message: str,
    table_id: str | None = None,
    target_role: str | None = None,
) -> AIEventOut:
    event = AIEvent(
        id=new_id(),
        table_id=table_id,
        event_type=event_type,
        message=message,
        target_role=target_role,
        resolved=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return ai_event_to_out(event)


def list_alerts(db: Session, resolved: bool = False, user_role: str | None = None) -> list[AIEventOut]:
    q = db.query(AIEvent).filter(AIEvent.resolved == resolved)
    if user_role and user_role in ROLE_FILTER:
        q = q.filter(AIEvent.event_type.in_(ROLE_FILTER[user_role]))
    events = q.order_by(AIEvent.created_at.desc()).all()
    return [ai_event_to_out(e) for e in events]


def resolve_alert(db: Session, event_id: str) -> dict[str, str | bool]:
    event = db.get(AIEvent, event_id)
    if not event:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    event.resolved = True
    db.commit()
    return {"id": event_id, "resolved": True}
