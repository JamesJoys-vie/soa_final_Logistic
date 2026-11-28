"""Unit of Work: puts the three repositories in one transaction that commits or rolls back together."""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.database import Database
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.trip_repository import TripRepository
from app.repositories.vehicle_repository import VehicleRepository


class UnitOfWork:
    def __init__(self, conn: sqlite3.Connection):
        self.vehicles = VehicleRepository(conn)
        self.trips = TripRepository(conn)
        self.assignments = AssignmentRepository(conn)


class UnitOfWorkFactory:
    def __init__(self, database: Database):
        self._database = database

    @contextmanager
    def read(self) -> Iterator[UnitOfWork]:
        with self._database.read() as conn:
            yield UnitOfWork(conn)

    @contextmanager
    def transaction(self) -> Iterator[UnitOfWork]:
        with self._database.transaction() as conn:
            yield UnitOfWork(conn)
