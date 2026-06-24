from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_floor_editor
from app.database import get_db
from app.models.user import User
from app.schemas.floor import CreateTableIn, StatusPatchIn, TableOut, TablePatchIn
from app.services import table_service

router = APIRouter(prefix="/tables", tags=["tables"])


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
