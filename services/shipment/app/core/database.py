"""Shipment's own SQLite connection (one .db file that no other service opens).

- WAL: readers do not block the writer.
- busy_timeout: a second writer waits up to 5 seconds instead of failing at once.
- BEGIN IMMEDIATE: takes the write lock at the start, so "read - check - write" is atomic.
"""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

INIT_SQL = Path(__file__).resolve().parents[2] / "init.sql"


class Database:
    def __init__(self, path: str):
        self._path = path

    def init_schema(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with self.read() as conn:
            conn.executescript(INIT_SQL.read_text(encoding="utf-8"))

    def is_up(self) -> bool:
        try:
            with self.read() as conn:
                conn.execute("SELECT 1 FROM vehicles LIMIT 1")
            return True
        except sqlite3.Error:
            return False

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.read() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, isolation_level=None)  # BEGIN / COMMIT are managed explicitly
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
