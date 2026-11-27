from dataclasses import dataclass

from app.domain.enums import TripDirection
from app.domain.line_item import LineItem


@dataclass(frozen=True)
class Trip:
    """An inbound trip (IN, receiving) or an outbound trip (OUT, shipping) with its goods."""
    id: int
    vehicle_id: int
    plate: str
    driver_name: str
    direction: TripDirection
    destination: str | None
    assignment_id: int | None
    created_at: str
    closed_at: str | None
    lines: list[LineItem]
