from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.ids import new_id
from app.models import Bill, CleaningEvent, DiningSession, MenuItem, Order, OrderItem, Table
from app.schemas.order import BillOut, BillItemOut, OrderItemOut, OrderOut, PlaceOrderIn
from app.services.table_service import _emit_table_updated, record_history
from app.socket_manager import sio


def _fmt_dt(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat().replace("+00:00", "Z")


def _order_to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        session_id=order.session_id,
        table_id=order.table_id,
        placed_at=_fmt_dt(order.placed_at),
        status=order.status,
        items=[
            OrderItemOut(
                id=i.id,
                item_name=i.item_name,
                unit_price=float(i.unit_price),
                quantity=i.quantity,
            )
            for i in order.items
        ],
    )


def list_orders(db: Session, table_id: str | None = None, session_id: str | None = None) -> list[OrderOut]:
    q = db.query(Order)
    if table_id:
        q = q.filter(Order.table_id == table_id)
    if session_id:
        q = q.filter(Order.session_id == session_id)
    orders = q.order_by(Order.placed_at.desc()).all()
    return [_order_to_out(o) for o in orders]


def place_order(db: Session, payload: PlaceOrderIn) -> OrderOut:
    table = db.get(Table, payload.table_id)
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    session = None
    if payload.session_id:
        session = db.get(DiningSession, payload.session_id)
    if not session:
        session = (
            db.query(DiningSession)
            .filter(
                DiningSession.table_id == payload.table_id,
                DiningSession.status.in_(("SEATED", "ACTIVE", "BILLING")),
            )
            .order_by(DiningSession.seated_at.desc())
            .first()
        )
    if not session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active session for table")
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No items in order")

    now = datetime.now(timezone.utc)
    order = Order(
        id=new_id(),
        session_id=session.id,
        table_id=payload.table_id,
        placed_at=now,
        status="RECEIVED",
    )
    db.add(order)

    for line in payload.items:
        menu_item = db.get(MenuItem, line.menu_item_id)
        if not menu_item or not menu_item.available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Menu item unavailable")
        db.add(
            OrderItem(
                id=new_id(),
                order_id=order.id,
                menu_item_id=menu_item.id,
                item_name=menu_item.name,
                unit_price=float(menu_item.price),
                quantity=line.quantity,
            )
        )

    if table.status == "SEATED":
        old = table.status
        table.status = "ACTIVE"
        session.status = "ACTIVE"
        record_history(db, table.id, old, "ACTIVE", None, session.id)

    db.commit()
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order.id).one()
    db.refresh(table)

    order_out = _order_to_out(order)
    sio.emit_sync("order_placed", order_out.model_dump(by_alias=True), room=str(table.floor_id))
    _emit_table_updated(table)
    return order_out


def _bill_items_for_session(db: Session, session_id: str) -> list[BillItemOut]:
    rows = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.session_id == session_id)
        .all()
    )
    aggregated: dict[str, BillItemOut] = {}
    for row in rows:
        key = row.item_name
        line_total = float(row.unit_price) * row.quantity
        if key in aggregated:
            existing = aggregated[key]
            aggregated[key] = BillItemOut(
                item_name=existing.item_name,
                unit_price=existing.unit_price,
                quantity=existing.quantity + row.quantity,
                line_total=existing.line_total + line_total,
            )
        else:
            aggregated[key] = BillItemOut(
                item_name=row.item_name,
                unit_price=float(row.unit_price),
                quantity=row.quantity,
                line_total=line_total,
            )
    return list(aggregated.values())


def _bill_to_out(bill: Bill, items: list[BillItemOut]) -> BillOut:
    return BillOut(
        id=bill.id,
        session_id=bill.session_id,
        subtotal=float(bill.subtotal),
        total=float(bill.total),
        status=bill.status,
        generated_at=_fmt_dt(bill.generated_at),
        paid_at=_fmt_dt(bill.paid_at) if bill.paid_at else None,
        items=items,
    )


def request_bill(db: Session, session_id: str, user_id: str | None) -> BillOut:
    session = db.get(DiningSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    table = db.get(Table, session.table_id)
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    existing = db.query(Bill).filter(Bill.session_id == session_id).first()
    items = _bill_items_for_session(db, session_id)
    subtotal = sum(i.line_total for i in items)
    total = subtotal

    if existing:
        bill = existing
    else:
        bill = Bill(
            id=new_id(),
            session_id=session_id,
            subtotal=subtotal,
            total=total,
            generated_at=datetime.now(timezone.utc),
            status="OPEN",
        )
        db.add(bill)

    if table.status in ("SEATED", "ACTIVE"):
        old = table.status
        table.status = "BILLING"
        session.status = "BILLING"
        record_history(db, table.id, old, "BILLING", user_id, session.id)

    db.commit()
    db.refresh(bill)
    if table:
        db.refresh(table)
        _emit_table_updated(table)
    return _bill_to_out(bill, items)


def get_bill(db: Session, session_id: str) -> BillOut:
    bill = db.query(Bill).filter(Bill.session_id == session_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    items = _bill_items_for_session(db, session_id)
    return _bill_to_out(bill, items)


def mark_paid(db: Session, session_id: str, user_id: str | None) -> BillOut:
    session = db.get(DiningSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    bill = db.query(Bill).filter(Bill.session_id == session_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    table = db.get(Table, session.table_id)
    now = datetime.now(timezone.utc)

    bill.status = "PAID"
    bill.paid_at = now
    session.payment_method = "CASH"

    if table:
        if table.status == "BILLING":
            old = table.status
            table.status = "PAID"
            session.status = "PAID"
            record_history(db, table.id, old, "PAID", user_id, session.id)
            old = table.status
            table.status = "CLEANING"
            session.status = "CLEANING"
            table.cleaning_started_at = now.isoformat().replace("+00:00", "Z")
            record_history(db, table.id, old, "CLEANING", user_id, session.id)
            db.add(
                CleaningEvent(
                    id=new_id(),
                    table_id=table.id,
                    dining_session_id=session.id,
                    status="REQUESTED",
                    requested_at=now,
                )
            )
        session.closed_at = now

    db.commit()
    db.refresh(bill)
    items = _bill_items_for_session(db, session_id)
    if table:
        db.refresh(table)
        sio.emit_sync(
            "payment_confirmed",
            {"sessionId": session_id, "tableId": table.id, "total": float(bill.total)},
            room=str(table.floor_id),
        )
        _emit_table_updated(table)
    return _bill_to_out(bill, items)
