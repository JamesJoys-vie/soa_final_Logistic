"""Vehicle and its state machine: 7 states, 3 display groups (section 5 of the assignment)."""
from dataclasses import dataclass

from app.core.errors import Conflict
from app.domain.enums import VehicleGroup, VehicleStatus

_GROUP = {
    VehicleStatus.ARRIVING: VehicleGroup.INBOUND,
    VehicleStatus.WAITING_UNLOAD: VehicleGroup.INBOUND,
    VehicleStatus.UNLOADING: VehicleGroup.INBOUND,
    VehicleStatus.IDLE: VehicleGroup.IDLE,
    VehicleStatus.WAITING_LOAD: VehicleGroup.OUTBOUND,
    VehicleStatus.LOADING: VehicleGroup.OUTBOUND,
    VehicleStatus.DEPARTED: VehicleGroup.OUTBOUND,
}

# The next step a user may move to. IDLE -> WAITING_LOAD is not here:
# only the system does it, when an assignment is confirmed or auto-approved.
_NEXT_STEP = {
    VehicleStatus.ARRIVING: VehicleStatus.WAITING_UNLOAD,
    VehicleStatus.WAITING_UNLOAD: VehicleStatus.UNLOADING,
    VehicleStatus.UNLOADING: VehicleStatus.IDLE,
    VehicleStatus.WAITING_LOAD: VehicleStatus.LOADING,
    VehicleStatus.LOADING: VehicleStatus.DEPARTED,
}


@dataclass(frozen=True)
class Vehicle:
    id: int
    plate: str
    driver_name: str
    status: VehicleStatus

    @property
    def group(self) -> VehicleGroup:
        return _GROUP[self.status]

    @property
    def next_status(self) -> VehicleStatus | None:
        return _NEXT_STEP.get(self.status)

    def ensure_can_move_to(self, target: VehicleStatus) -> None:
        if target != self.next_status:
            raise Conflict("Chuyển trạng thái xe không hợp lệ", code="INVALID_TRANSITION",
                           details={"from": self.status, "to": target, "allowed": self.next_status})

    def ensure_assignable(self) -> None:
        if self.status != VehicleStatus.IDLE:
            raise Conflict("Chỉ gán hàng cho xe đang trống", code="VEHICLE_NOT_IDLE",
                           details={"vehicle_id": self.id, "status": self.status})
