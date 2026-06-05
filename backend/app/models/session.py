from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiningSession(Base):
    __tablename__ = "dining_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    table_id: Mapped[str] = mapped_column(String(64), ForeignKey("tables.id"), index=True)
    guest_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    party_size: Mapped[int] = mapped_column(Integer)
    seated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20))
    host_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
