"""In-memory FAKE Inventory, only for testing and trying out Shipment.

Author: Phan Huy Bính (524H0081).

Behaviour copied from the real Inventory by Nguyễn Đức Hiệu (branch Hieu, services/inventory):
- available = on_hand - allocated - reserved; all-or-nothing reservation, one short line gives
  409 STOCK_INSUFFICIENT with a list of {item_id, requested, available, missing};
- reserving the same assignment_id again: ACTIVE returns the existing one, committed / released gives
  409 ASSIGNMENT_ALREADY_PROCESSED;
- releasing something never reserved: 404 (Shipment's client treats it as nothing to release);
  releasing a committed reservation: 409 INVALID_STATUS.
One difference: receipts / departures here are idempotent by trip_id, as the plan requires.
"""
import json
import threading
from pathlib import Path

from app.clients.inventory_gateway import InventoryGateway
from app.core.errors import Conflict, NotFound, UpstreamError
from app.domain.line_item import LineItem


class FakeInventory(InventoryGateway):
    def __init__(self, items: list[dict]):
        self._lock = threading.Lock()
        self.items = items
        stock = {item["id"]: item["initial_stock"] for item in items}
        self.on_hand = {i: s["on_hand"] for i, s in stock.items()}
        self.incoming = {i: s["incoming"] for i, s in stock.items()}
        self.allocated = {i: s["allocated"] for i, s in stock.items()}
        self.reserved = {i: s["reserved"] for i, s in stock.items()}
        self.reservations: dict[int, tuple[str, list[LineItem]]] = {}  # assignment_id -> (status, lines)
        self._done_trips: set[tuple[str, int]] = set()
        self.is_down = False

    @classmethod
    def from_seed(cls, seed_path: str | Path) -> "FakeInventory":
        return cls(json.loads(Path(seed_path).read_text(encoding="utf-8"))["items"])

    def available(self, item_id: int) -> int:
        return self.on_hand.get(item_id, 0) - self.allocated.get(item_id, 0) - self.reserved.get(item_id, 0)

    def status_of(self, assignment_id: int) -> str | None:
        return self.reservations[assignment_id][0] if assignment_id in self.reservations else None

    # ---- InventoryGateway ------------------------------------------------------------
    def reserve(self, assignment_id: int, lines: list[LineItem]) -> None:
        with self._online():
            status = self.status_of(assignment_id)
            if status == "ACTIVE":
                return
            if status is not None:
                raise Conflict(f"Lần gán {assignment_id} đã ở trạng thái {status}", code="ASSIGNMENT_ALREADY_PROCESSED")
            missing = []
            for line in sorted(lines, key=lambda x: x.item_id):
                available = max(0, self.available(line.item_id))
                if line.boxes > available:
                    missing.append({"item_id": line.item_id, "requested": line.boxes, "available": available,
                                    "missing": line.boxes - available})
            if missing:
                raise Conflict("Không đủ tồn kho khả dụng để thực hiện giữ chỗ trọn gói",
                               code="STOCK_INSUFFICIENT", details=missing)
            for line in lines:
                self.reserved[line.item_id] += line.boxes
            self.reservations[assignment_id] = ("ACTIVE", lines)

    def commit(self, assignment_id: int) -> None:
        with self._online():
            status = self.status_of(assignment_id)
            if status is None:
                raise NotFound("Không tìm thấy giữ chỗ", code="RESERVATION_NOT_FOUND")
            if status == "COMMITTED":
                return
            if status != "ACTIVE":
                raise Conflict(f"Không thể chốt giữ chỗ ở trạng thái {status}", code="INVALID_STATUS")
            lines = self.reservations[assignment_id][1]
            for line in lines:
                self.reserved[line.item_id] -= line.boxes
                self.allocated[line.item_id] += line.boxes
            self.reservations[assignment_id] = ("COMMITTED", lines)

    def release(self, assignment_id: int) -> None:
        with self._online():
            status = self.status_of(assignment_id)
            if status is None or status == "RELEASED":  # never reserved: real API gives 404, client treats it as done
                return
            if status != "ACTIVE":
                raise Conflict(f"Không thể nhả giữ chỗ ở trạng thái {status}", code="INVALID_STATUS")
            lines = self.reservations[assignment_id][1]
            for line in lines:
                self.reserved[line.item_id] -= line.boxes
            self.reservations[assignment_id] = ("RELEASED", lines)

    def receive(self, trip_id: int, lines: list[LineItem]) -> None:
        with self._online():
            if self._first_time(("RECEIPT", trip_id)):
                for line in lines:
                    self.incoming[line.item_id] -= line.boxes
                    self.on_hand[line.item_id] += line.boxes

    def depart(self, trip_id: int, lines: list[LineItem]) -> None:
        with self._online():
            if self._first_time(("DEPARTURE", trip_id)):
                for line in lines:
                    self.allocated[line.item_id] -= line.boxes
                    self.on_hand[line.item_id] -= line.boxes

    def _first_time(self, key: tuple[str, int]) -> bool:
        if key in self._done_trips:
            return False
        self._done_trips.add(key)
        return True

    def _online(self) -> threading.Lock:
        if self.is_down:
            raise UpstreamError("Inventory giả lập đang tắt", code="INVENTORY_ERROR")
        return self._lock
