"""The port Shipment needs from Inventory. Business logic depends only on this abstraction."""
from abc import ABC, abstractmethod

from app.domain.line_item import LineItem


class InventoryGateway(ABC):
    """The five internal Inventory APIs the plan assigns to Shipment. The plan requires all of them to be idempotent."""

    @abstractmethod
    def reserve(self, assignment_id: int, lines: list[LineItem]) -> None:
        """All-or-nothing reservation. If one line is short: Conflict with the short lines, nothing is reserved."""

    @abstractmethod
    def commit(self, assignment_id: int) -> None:
        """Commit the reservation: reserved moves to allocated."""

    @abstractmethod
    def release(self, assignment_id: int) -> None:
        """Release the reservation. Does nothing if it was never reserved."""

    @abstractmethod
    def receive(self, trip_id: int, lines: list[LineItem]) -> None:
        """Vehicle finished unloading: incoming moves to on_hand."""

    @abstractmethod
    def depart(self, trip_id: int, lines: list[LineItem]) -> None:
        """Vehicle left the warehouse: subtract the outbound trip lines from allocated and on_hand."""
