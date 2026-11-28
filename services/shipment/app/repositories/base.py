import sqlite3
from collections.abc import Iterable

from app.domain.line_item import LineItem


class BaseRepository:
    """Base class: holds the current transaction's connection and shared line-item helpers."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _lines(self, table: str, owner_column: str, owner_ids: Iterable[int]) -> dict[int, list[LineItem]]:
        lines: dict[int, list[LineItem]] = {owner_id: [] for owner_id in owner_ids}
        if lines:
            marks = ",".join("?" * len(lines))
            rows = self._conn.execute(
                f"SELECT {owner_column} AS owner, item_id, boxes FROM {table}"
                f" WHERE {owner_column} IN ({marks}) ORDER BY item_id", list(lines))
            for row in rows:
                lines[row["owner"]].append(LineItem(row["item_id"], row["boxes"]))
        return lines

    def _insert_lines(self, table: str, owner_column: str, owner_id: int, lines: Iterable[LineItem]) -> None:
        self._conn.executemany(
            f"INSERT INTO {table} ({owner_column}, item_id, boxes) VALUES (?, ?, ?)",
            [(owner_id, line.item_id, line.boxes) for line in lines])
