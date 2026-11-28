import sqlite3
from collections.abc import Iterable

from app.domain.enums import VehicleStatus
from app.domain.vehicle import Vehicle
from app.repositories.base import BaseRepository


class VehicleRepository(BaseRepository):
    """Tables vehicles and vehicle_status_history."""

    def get(self, vehicle_id: int) -> Vehicle | None:
        row = self._conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        return self._to_vehicle(row) if row else None

    def find(self, statuses: Iterable[VehicleStatus]) -> list[Vehicle]:
        values = list(statuses)
        marks = ",".join("?" * len(values))
        rows = self._conn.execute(f"SELECT * FROM vehicles WHERE status IN ({marks}) ORDER BY id", values)
        return [self._to_vehicle(row) for row in rows]

    def add(self, vehicle: Vehicle) -> None:
        self._conn.execute("INSERT INTO vehicles (id, plate, driver_name, status) VALUES (?, ?, ?, ?)",
                           (vehicle.id, vehicle.plate, vehicle.driver_name, vehicle.status))

    def move(self, vehicle_id: int, source: VehicleStatus, target: VehicleStatus, *,
             changed_by: str | None, now: str) -> bool:
        """CONDITIONAL status change plus history row. False = someone else changed it first."""
        cursor = self._conn.execute("UPDATE vehicles SET status = ? WHERE id = ? AND status = ?",
                                    (target, vehicle_id, source))
        if cursor.rowcount == 0:
            return False
        self._conn.execute(
            "INSERT INTO vehicle_status_history (vehicle_id, from_status, to_status, changed_by, changed_at)"
            " VALUES (?, ?, ?, ?, ?)", (vehicle_id, source, target, changed_by, now))
        return True

    def count_by_status(self) -> dict[str, int]:
        counts = {status.value: 0 for status in VehicleStatus}
        for row in self._conn.execute("SELECT status, COUNT(*) AS total FROM vehicles GROUP BY status"):
            counts[row["status"]] = row["total"]
        return counts

    @staticmethod
    def _to_vehicle(row: sqlite3.Row) -> Vehicle:
        return Vehicle(row["id"], row["plate"], row["driver_name"], VehicleStatus(row["status"]))
