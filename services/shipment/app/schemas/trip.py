from pydantic import BaseModel, ConfigDict

from app.domain.enums import TripDirection
from app.schemas.common import LineSchema


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int
    plate: str
    driver_name: str
    direction: TripDirection
    destination: str | None
    assignment_id: int | None
    created_at: str
    closed_at: str | None
    lines: list[LineSchema]
