from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, require_floor_editor
from app.database import get_db
from app.models import TableQRCode
from app.models.user import User
from app.schemas.floor import CreateTableIn, StatusPatchIn, TableOut, TablePatchIn
from app.services import table_service

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("/{table_id}/qr")
def table_qr_page(table_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    qr = (
        db.query(TableQRCode)
        .filter(TableQRCode.table_id == table_id, TableQRCode.is_active.is_(True))
        .first()
    )
    if not qr:
        raise HTTPException(404, "QR code not found for table")
    guest_url = f"{settings.guest_menu_base_url}/guest/menu?token={qr.token}"
    qr_img = f"https://api.qrserver.com/v1/create-qr-code/?size=240x240&data={quote(guest_url)}"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Table QR</title>
<style>
  body {{ font-family: system-ui, sans-serif; text-align: center; padding: 40px; }}
  img {{ border: 8px solid #111; border-radius: 8px; }}
  p {{ color: #555; margin-top: 16px; word-break: break-all; }}
</style></head>
<body>
  <h1>Scan to order</h1>
  <img src="{qr_img}" alt="QR code" width="240" height="240" />
  <p>{guest_url}</p>
</body></html>"""
    return HTMLResponse(html)


@router.post("", response_model=TableOut)
def create_table(
    body: CreateTableIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_floor_editor),
) -> TableOut:
    return table_service.add_table(db, body)


@router.put("/{table_id}", response_model=TableOut)
def update_table(
    table_id: str,
    body: TablePatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TableOut:
    return table_service.update_table(db, table_id, body)


@router.patch("/{table_id}/status", response_model=TableOut)
def patch_status(
    table_id: str,
    body: StatusPatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TableOut:
    return table_service.patch_table_status(db, table_id, body.status, user.id)


@router.delete("/{table_id}", status_code=204)
def remove_table(
    table_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_floor_editor),
) -> None:
    table_service.delete_table(db, table_id)
