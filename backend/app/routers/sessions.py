from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.session import DiningSessionOut, SeatGuestIn
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[DiningSessionOut])
def get_sessions(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[DiningSessionOut]:
    return session_service.list_sessions(db)


@router.post("/seat", response_model=DiningSessionOut)
def seat(
    body: SeatGuestIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DiningSessionOut:
    return session_service.seat_guest(db, body, user.id)


@router.post("/{session_id}/close", response_model=DiningSessionOut)
def close(
    session_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DiningSessionOut:
    return session_service.close_session(db, session_id, user.id)
