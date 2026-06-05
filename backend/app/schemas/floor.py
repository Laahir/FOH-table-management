from app.schemas.common import CamelModel


class RectBounds(CamelModel):
    x: float
    y: float
    width: float
    height: float


class SectionOut(CamelModel):
    id: str
    name: str
    color: str
    bounds: RectBounds


class FloorLabelOut(CamelModel):
    id: str
    kind: str
    text: str
    bounds: RectBounds


class TableOut(CamelModel):
    id: str
    section_id: str
    number: str
    capacity: int
    type: str
    shape: str
    status: str
    x: float
    y: float
    width: float
    height: float
    rotation: float


class FloorOut(CamelModel):
    id: str
    name: str
    width: int
    height: int
    sections: list[SectionOut]
    labels: list[FloorLabelOut]
    tables: list[TableOut]


class CreateTableIn(CamelModel):
    number: str
    capacity: int
    section_id: str
    type: str
    shape: str
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None


class TablePatchIn(CamelModel):
    section_id: str | None = None
    number: str | None = None
    capacity: int | None = None
    type: str | None = None
    shape: str | None = None
    status: str | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    rotation: float | None = None


class StatusPatchIn(CamelModel):
    status: str
