"""Inbound and outbound trips for managers (section 3 of the assignment)."""
from app.core.errors import NotFound
from app.domain.enums import TripDirection
from app.domain.trip import Trip
from app.repositories.unit_of_work import UnitOfWorkFactory


class TripService:
    def __init__(self, uow: UnitOfWorkFactory):
        self._uow = uow

    def find(self, direction: TripDirection | None) -> list[Trip]:
        with self._uow.read() as uow:
            return uow.trips.find(direction)

    def get(self, trip_id: int) -> Trip:
        with self._uow.read() as uow:
            trip = uow.trips.get(trip_id)
        if trip is None:
            raise NotFound("Không tìm thấy lượt xe", details={"trip_id": trip_id})
        return trip
