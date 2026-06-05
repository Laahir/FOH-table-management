import time
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import DiningSession, Floor, Table
from app.schemas.floor import FloorOut, TableOut
from app.seed import empty_floor_layout


def _table_to_out(table: Table) -> TableOut:
    return TableOut(
        id=table.id,
        section_id=table.section_id,
        number=table.number,
        capacity=table.capacity,
        type=table.type,
        shape=table.shape,
        status=table.status,
        x=table.x,
        y=table.y,
        width=table.width,
        height=table.height,
        rotation=table.rotation,
    )


def floor_to_out(floor: Floor) -> FloorOut:
    return FloorOut(
        id=floor.id,
        name=floor.name,
        width=floor.width,
        height=floor.height,
        sections=floor.sections,
        labels=floor.labels,
        tables=[_table_to_out(t) for t in floor.tables],
    )


def get_current_floor(db: Session) -> Floor:
    floor = db.query(Floor).first()
    if not floor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found")
    return floor


def update_floor(db: Session, payload: FloorOut) -> FloorOut:
    floor = get_current_floor(db)
    floor.name = payload.name
    floor.width = payload.width
    floor.height = payload.height
    floor.sections = [s.model_dump(by_alias=True) for s in payload.sections]
    floor.labels = [l.model_dump(by_alias=True) for l in payload.labels]

    incoming_ids = {t.id for t in payload.tables}
    existing = {t.id: t for t in floor.tables}

    for table_id, table in list(existing.items()):
        if table_id not in incoming_ids:
            db.delete(table)

    for t in payload.tables:
        data = {
            "section_id": t.section_id,
            "number": t.number,
            "capacity": t.capacity,
            "type": t.type,
            "shape": t.shape,
            "status": t.status,
            "x": t.x,
            "y": t.y,
            "width": t.width,
            "height": t.height,
            "rotation": t.rotation,
        }
        if t.id in existing:
            for key, val in data.items():
                setattr(existing[t.id], key, val)
        else:
            db.add(Table(id=t.id, floor_id=floor.id, **data))

    db.commit()
    db.refresh(floor)
    return floor_to_out(floor)


def reset_floor(db: Session) -> FloorOut:
    floor = get_current_floor(db)
    empty_floor_layout(floor)
    for table in list(floor.tables):
        db.delete(table)
    db.query(DiningSession).delete()
    db.commit()
    db.refresh(floor)
    return floor_to_out(floor)
