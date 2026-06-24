from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.core.security import hash_password
from app.models import DiningSession, Floor, MenuItem, Reservation, StatusHistory, Table, TableQRCode, User
from app.seed_data import DEMO_PASSWORD, DEMO_USERS, INITIAL_FLOOR, DEMO_MENU_ITEMS


def seed_database(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    now = datetime.now(timezone.utc)

    for u in DEMO_USERS:
        db.add(
            User(
                id=u["id"],
                name=u["name"],
                email=u["email"],
                role=u["role"],
                password_hash=hash_password(DEMO_PASSWORD),
                is_active=True,
                created_at=now,
            )
        )

    floor = Floor(
        id=INITIAL_FLOOR["id"],
        name=INITIAL_FLOOR["name"],
        width=INITIAL_FLOOR["width"],
        height=INITIAL_FLOOR["height"],
        sections=INITIAL_FLOOR["sections"],
        labels=INITIAL_FLOOR["labels"],
    )
    db.add(floor)

    for t in INITIAL_FLOOR["tables"]:
        table = Table(
            id=t["id"],
            floor_id=floor.id,
            section_id=t["sectionId"],
            number=t["number"],
            capacity=t["capacity"],
            type=t["type"],
            shape=t["shape"],
            status=t["status"],
            x=t["x"],
            y=t["y"],
            width=t["width"],
            height=t["height"],
            rotation=t["rotation"],
        )
        db.add(table)
        # generate a QR token for every table
        db.add(TableQRCode(id=new_id(), table_id=t["id"], token=new_id(), is_active=True))

    for item in DEMO_MENU_ITEMS:
        db.add(MenuItem(**item, id=new_id()))

    db.commit()


def empty_floor_layout(floor: Floor) -> None:
    w, h = floor.width, floor.height
    floor.sections = []
    floor.labels = [
        {
            "id": f"lbl-{new_id()}-ent",
            "kind": "ENTRANCE",
            "text": "Entrance",
            "bounds": {"x": w / 2 - 100, "y": h - 56, "width": 200, "height": 44},
        },
        {
            "id": f"lbl-{new_id()}-kit",
            "kind": "KITCHEN",
            "text": "Kitchen",
            "bounds": {"x": w - 140, "y": 12, "width": 120, "height": 44},
        },
    ]
