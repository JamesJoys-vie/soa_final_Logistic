"""Vehicle status (section 5 of the assignment). Two transitions change stock in Inventory."""
from app.clients.inventory_gateway import InventoryGateway
from app.core.clock import Clock
from app.core.errors import Conflict, NotFound
from app.domain.enums import TripDirection, VehicleStatus
from app.domain.trip import Trip
from app.domain.user import CurrentUser
from app.domain.vehicle import Vehicle
from app.repositories.unit_of_work import UnitOfWorkFactory


class VehicleService:
    def __init__(self, uow: UnitOfWorkFactory, inventory: InventoryGateway, clock: Clock):
        self._uow = uow
        self._inventory = inventory
        self._clock = clock
        self._stock_effects = {
            (VehicleStatus.UNLOADING, VehicleStatus.IDLE): self._receive_goods,
            (VehicleStatus.LOADING, VehicleStatus.DEPARTED): self._ship_goods,
        }

    def find(self, statuses: list[VehicleStatus] | None) -> list[tuple[Vehicle, int | None]]:
        """Vehicles with the ID of the PENDING assignment locking each one, if any."""
        with self._uow.read() as uow:
            locks = uow.assignments.pending_ids_by_vehicle()
            return [(vehicle, locks.get(vehicle.id)) for vehicle in uow.vehicles.find(statuses or VehicleStatus)]

    def change_status(self, user: CurrentUser, vehicle_id: int, target: VehicleStatus) -> Vehicle:
        """Call Inventory FIRST (idempotent), then the conditional UPDATE.

        Inventory fails: the vehicle keeps its state and the user can retry.
        Two users at once: Inventory records it once, one wins in Shipment, the other gets 409.
        """
        with self._uow.read() as uow:
            vehicle = uow.vehicles.get(vehicle_id)
        if vehicle is None:
            raise NotFound("Không tìm thấy xe", details={"vehicle_id": vehicle_id})
        vehicle.ensure_can_move_to(target)
        effect = self._stock_effects.get((vehicle.status, target))
        trip = effect(vehicle_id) if effect else None

        now = self._clock.now_iso()
        with self._uow.transaction() as uow:
            if not uow.vehicles.move(vehicle_id, vehicle.status, target, changed_by=user.id, now=now):
                raise Conflict("Trạng thái xe đã bị người khác thay đổi", code="VEHICLE_STATUS_CHANGED",
                               details={"vehicle_id": vehicle_id, "expected": vehicle.status})
            if trip:
                uow.trips.close(trip.id, now)
            return uow.vehicles.get(vehicle_id)

    def _receive_goods(self, vehicle_id: int) -> Trip:
        trip = self._open_trip(vehicle_id, TripDirection.IN)
        self._inventory.receive(trip.id, trip.lines)
        return trip

    def _ship_goods(self, vehicle_id: int) -> Trip:
        trip = self._open_trip(vehicle_id, TripDirection.OUT)
        self._inventory.depart(trip.id, trip.lines)
        return trip

    def _open_trip(self, vehicle_id: int, direction: TripDirection) -> Trip:
        with self._uow.read() as uow:
            trip = uow.trips.find_open(vehicle_id, direction)
        if trip is None:
            raise Conflict("Xe không có lượt đang mở", code="NO_OPEN_TRIP",
                           details={"vehicle_id": vehicle_id, "direction": direction})
        return trip
