import sqlite3

from app.domain.enums import TripDirection
from app.domain.line_item import LineItem
from app.domain.trip import Trip
from app.repositories.base import BaseRepository

_SELECT = "SELECT t.*, v.plate, v.driver_name FROM trips t JOIN vehicles v ON v.id = t.vehicle_id"


class TripRepository(BaseRepository):
    """Tables trips and trip_lines."""

    def get(self, trip_id: int) -> Trip | None:
        return self._first(f"{_SELECT} WHERE t.id = ?", (trip_id,))

    def find(self, direction: TripDirection | None) -> list[Trip]:
        where, params = (" WHERE t.direction = ?", (direction,)) if direction else ("", ())
        return self._all(f"{_SELECT}{where} ORDER BY t.created_at DESC, t.id DESC", params)

    def find_open(self, vehicle_id: int, direction: TripDirection) -> Trip | None:
        return self._first(f"{_SELECT} WHERE t.vehicle_id = ? AND t.direction = ? AND t.closed_at IS NULL"
                           " ORDER BY t.id DESC LIMIT 1", (vehicle_id, direction))

    def add(self, *, vehicle_id: int, direction: TripDirection, lines: list[LineItem], created_at: str,
            destination: str | None = None, assignment_id: int | None = None, closed_at: str | None = None,
            trip_id: int | None = None) -> None:
        new_id = self._conn.execute(
            "INSERT INTO trips (id, vehicle_id, direction, destination, assignment_id, created_at, closed_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trip_id, vehicle_id, direction, destination, assignment_id, created_at, closed_at)).lastrowid
        self._insert_lines("trip_lines", "trip_id", new_id, lines)

    def close(self, trip_id: int, now: str) -> None:
        self._conn.execute("UPDATE trips SET closed_at = ? WHERE id = ? AND closed_at IS NULL", (now, trip_id))

    def _first(self, sql: str, params: tuple) -> Trip | None:
        trips = self._all(sql, params)
        return trips[0] if trips else None

    def _all(self, sql: str, params: tuple) -> list[Trip]:
        rows = self._conn.execute(sql, params).fetchall()
        lines = self._lines("trip_lines", "trip_id", [row["id"] for row in rows])
        return [self._to_trip(row, lines[row["id"]]) for row in rows]

    @staticmethod
    def _to_trip(row: sqlite3.Row, lines: list[LineItem]) -> Trip:
        return Trip(id=row["id"], vehicle_id=row["vehicle_id"], plate=row["plate"], driver_name=row["driver_name"],
                    direction=TripDirection(row["direction"]), destination=row["destination"],
                    assignment_id=row["assignment_id"], created_at=row["created_at"], closed_at=row["closed_at"],
                    lines=lines)
