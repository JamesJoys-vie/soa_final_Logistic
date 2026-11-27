"""REST implementation of InventoryGateway, matching the internal API of the Inventory service (Nguyễn Đức Hiệu).

Inventory takes assignment_id and trip_id as strings (TEXT), so Shipment converts them before sending.
"""
from app.clients.base import ServiceClient
from app.clients.inventory_gateway import InventoryGateway
from app.domain.line_item import LineItem


class InventoryClient(ServiceClient, InventoryGateway):
    target = "inventory"

    def reserve(self, assignment_id: int, lines: list[LineItem]) -> None:
        self._post("/internal/reservations", {"assignment_id": str(assignment_id), "lines": self._dump(lines)})

    def commit(self, assignment_id: int) -> None:
        self._post(f"/internal/reservations/{assignment_id}/commit")

    def release(self, assignment_id: int) -> None:
        # 404: Inventory never reserved stock for this assignment, so there is nothing to release
        self._post(f"/internal/reservations/{assignment_id}/release", ok_statuses=frozenset({404}))

    def receive(self, trip_id: int, lines: list[LineItem]) -> None:
        self._post("/internal/receipts", {"trip_id": str(trip_id), "lines": self._dump(lines)})

    def depart(self, trip_id: int, lines: list[LineItem]) -> None:
        self._post("/internal/departures", {"trip_id": str(trip_id), "lines": self._dump(lines)})

    @staticmethod
    def _dump(lines: list[LineItem]) -> list[dict]:
        """Always sorted by item_id, the row locking order the assignment requires in Inventory."""
        return [{"item_id": line.item_id, "boxes": line.boxes} for line in sorted(lines, key=lambda x: x.item_id)]
