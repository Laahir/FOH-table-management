from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import DiningSession, Floor, StatusHistory, Table, User
from app.seed_data import DEMO_PASSWORD, DEMO_USERS, INITIAL_FLOOR


def seed_database(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    for u in DEMO_USERS:
        db.add(
            User(
                id=u["id"],
                name=u["name"],
                email=u["email"],
                role=u["role"],
                password_hash=hash_password(DEMO_PASSWORD),
                is_active=True,
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
        db.add(
            Table(
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
        )

    db.commit()


def empty_floor_layout(floor: Floor) -> None:
    w, h = floor.width, floor.height
    floor.sections = []
    floor.labels = [
        {
            "id": f"lbl-{int(datetime.now(timezone.utc).timestamp() * 1000)}-ent",
            "kind": "ENTRANCE",
            "text": "Entrance",
            "bounds": {"x": w / 2 - 100, "y": h - 56, "width": 200, "height": 44},
        },
        {
            "id": f"lbl-{int(datetime.now(timezone.utc).timestamp() * 1000)}-kit",
            "kind": "KITCHEN",
            "text": "Kitchen",
            "bounds": {"x": w - 140, "y": 12, "width": 120, "height": 44},
        },
    ]
