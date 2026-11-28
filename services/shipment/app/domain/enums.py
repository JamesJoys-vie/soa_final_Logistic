"""Fixed business value sets."""
from enum import StrEnum


class Role(StrEnum):
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    AUTHORIZED_STAFF = "AUTHORIZED_STAFF"


class VehicleStatus(StrEnum):
    ARRIVING = "ARRIVING"              # on the way to the warehouse
    WAITING_UNLOAD = "WAITING_UNLOAD"  # waiting to unload
    UNLOADING = "UNLOADING"            # unloading
    IDLE = "IDLE"                      # empty at the warehouse
    WAITING_LOAD = "WAITING_LOAD"      # waiting to load
    LOADING = "LOADING"                # loading
    DEPARTED = "DEPARTED"              # left the warehouse


class VehicleGroup(StrEnum):
    INBOUND = "INBOUND"    # inbound trip
    IDLE = "IDLE"          # empty at the warehouse
    OUTBOUND = "OUTBOUND"  # outbound trip


class TripDirection(StrEnum):
    IN = "IN"
    OUT = "OUT"


class AssignmentStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    AUTO_APPROVED = "AUTO_APPROVED"


class ApprovalType(StrEnum):
    MANUAL = "MANUAL"    # confirmed or approved by a manager
    TIMEOUT = "TIMEOUT"  # deadline passed, auto-approved


class Decision(StrEnum):
    """A decision that has claimed a PENDING assignment, before Inventory has committed / released.

    The first four values match the final states. CANCELLED is internal only: it is unknown whether
    Inventory reserved stock, so it is released to be safe and the record is deleted. Users never saw it.
    """
    CONFIRMED = "CONFIRMED"
    AUTO_APPROVED = "AUTO_APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"

    @property
    def approves(self) -> bool:
        return self in (Decision.CONFIRMED, Decision.AUTO_APPROVED)

    @property
    def approval_type(self) -> ApprovalType | None:
        return {Decision.CONFIRMED: ApprovalType.MANUAL, Decision.AUTO_APPROVED: ApprovalType.TIMEOUT}.get(self)
