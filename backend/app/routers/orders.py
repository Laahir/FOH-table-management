from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderOut, PlaceOrderIn
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(
    table_id: str | None = Query(None),
    session_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[OrderOut]:
    return order_service.list_orders(db, table_id=table_id, session_id=session_id)


@router.post("", response_model=OrderOut)
def place_order(
    body: PlaceOrderIn,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> OrderOut:
    return order_service.place_order(db, body)
