"""Load seed/seed.json shared with Inventory. Idempotent: only loads when there are no vehicles yet."""
import json
import logging
from pathlib import Path

from app.domain.enums import TripDirection, VehicleStatus
from app.domain.line_item import LineItem
from app.domain.vehicle import Vehicle
from app.repositories.unit_of_work import UnitOfWorkFactory

log = logging.getLogger("shipment.seed")


class SeedService:
    def __init__(self, uow: UnitOfWorkFactory, seed_path: str):
        self._uow = uow
        self._seed_path = Path(seed_path)

    def load(self) -> bool:
        with self._uow.transaction() as uow:
            if uow.vehicles.find(VehicleStatus):
                return False
            data = json.loads(self._seed_path.read_text(encoding="utf-8"))
            for item in data["vehicles"]:
                uow.vehicles.add(Vehicle(item["id"], item["plate"], item["driver_name"],
                                         VehicleStatus(item["status"])))
            for item in data["trips"]:
                uow.trips.add(trip_id=item["id"], vehicle_id=item["vehicle_id"],
                              direction=TripDirection(item["direction"]), destination=item["destination"],
                              created_at=item["created_at"], closed_at=item["closed_at"],
                              lines=[LineItem(**line) for line in item["lines"]])
        log.info("seeded %s vehicles, %s trips", len(data["vehicles"]), len(data["trips"]))
        return True
