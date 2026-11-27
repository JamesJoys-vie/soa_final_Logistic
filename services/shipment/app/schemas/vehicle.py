from pydantic import BaseModel

from app.domain.enums import VehicleGroup, VehicleStatus
from app.domain.vehicle import Vehicle


class VehicleStatusIn(BaseModel):
    status: VehicleStatus


class VehicleOut(BaseModel):
    id: int
    plate: str
    driver_name: str
    status: VehicleStatus
    group: VehicleGroup
    next_status: VehicleStatus | None
    pending_assignment_id: int | None

    @classmethod
    def of(cls, vehicle: Vehicle, pending_assignment_id: int | None = None) -> "VehicleOut":
        return cls(id=vehicle.id, plate=vehicle.plate, driver_name=vehicle.driver_name, status=vehicle.status,
                   group=vehicle.group, next_status=vehicle.next_status, pending_assignment_id=pending_assignment_id)
