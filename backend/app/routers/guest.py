from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TableQRCode
from app.schemas.menu import MenuItemOut
from app.services import menu_service

router = APIRouter(tags=["guest"])


@router.get("/guest/menu", response_model=list[MenuItemOut])
def guest_menu(token: str = Query(...), db: Session = Depends(get_db)) -> list[MenuItemOut]:
    qr = (
        db.query(TableQRCode)
        .filter(TableQRCode.token == token, TableQRCode.is_active.is_(True))
        .first()
    )
    if not qr:
        raise HTTPException(404, "Invalid or expired QR token")
    return menu_service.list_available(db)
