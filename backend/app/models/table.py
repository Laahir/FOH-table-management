from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    floor_id: Mapped[str] = mapped_column(String(64), ForeignKey("floors.id"), index=True)
    section_id: Mapped[str] = mapped_column(String(64))
    number: Mapped[str] = mapped_column(String(32))
    capacity: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(20))
    shape: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE")
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    rotation: Mapped[float] = mapped_column(Float, default=0)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="tables")  # noqa: F821
