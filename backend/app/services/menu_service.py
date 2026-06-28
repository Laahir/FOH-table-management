from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.models import MenuItem
from app.schemas.menu import MenuItemCreate, MenuItemOut, MenuItemPatch


def _to_out(item: MenuItem) -> MenuItemOut:
    return MenuItemOut(
        id=item.id,
        name=item.name,
        description=item.description,
        price=float(item.price),
        category=item.category,
        available=item.available,
        display_order=item.display_order,
    )


def list_all(db: Session) -> list[MenuItemOut]:
    items = db.query(MenuItem).order_by(MenuItem.category, MenuItem.display_order).all()
    return [_to_out(i) for i in items]


def list_available(db: Session) -> list[MenuItemOut]:
    items = (
        db.query(MenuItem)
        .filter(MenuItem.available.is_(True))
        .order_by(MenuItem.category, MenuItem.display_order)
        .all()
    )
    return [_to_out(i) for i in items]


def create_item(db: Session, payload: MenuItemCreate) -> MenuItemOut:
    item = MenuItem(
        id=new_id(),
        name=payload.name,
        description=payload.description,
        price=payload.price,
        category=payload.category,
        available=payload.available,
        display_order=payload.display_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(item)


def update_item(db: Session, item_id: str, payload: MenuItemPatch) -> MenuItemOut:
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    for key, val in payload.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return _to_out(item)


def delete_item(db: Session, item_id: str) -> None:
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    db.delete(item)
    db.commit()


def toggle_item(db: Session, item_id: str) -> MenuItemOut:
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    item.available = not item.available
    db.commit()
    db.refresh(item)
    return _to_out(item)
