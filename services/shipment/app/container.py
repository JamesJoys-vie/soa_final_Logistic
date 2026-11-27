"""Composition root: the ONLY place that creates objects and wires dependencies (constructor injection)."""
import httpx

from app.clients.inventory_client import InventoryClient
from app.clients.inventory_gateway import InventoryGateway
from app.core.clock import Clock
from app.core.config import Settings
from app.core.database import Database
from app.core.metrics import Metrics
from app.core.security import TokenVerifier
from app.domain.assignment_policy import AssignmentPolicies
from app.repositories.unit_of_work import UnitOfWorkFactory
from app.services.assignment_service import AssignmentService
from app.services.seed_service import SeedService
from app.services.trip_service import TripService
from app.services.vehicle_service import VehicleService
from app.workers.assignment_expiry_worker import AssignmentExpiryWorker
from app.workers.decision_retry_worker import DecisionRetryWorker
from app.workers.periodic import WorkerScheduler


class Container:
    def __init__(self, settings: Settings, *, clock: Clock | None = None, inventory: InventoryGateway | None = None):
        self.clock = clock or Clock()
        self.metrics = Metrics()
        self.database = Database(settings.db_path)
        self.uow = UnitOfWorkFactory(self.database)
        self.token_verifier = TokenVerifier(settings.jwt_secret)
        self.inventory = inventory or InventoryClient(
            httpx.Client(base_url=settings.inventory_url, timeout=settings.http_timeout_sec),
            settings.internal_api_key, self.metrics)

        policies = AssignmentPolicies(settings.assign_confirm_ttl_sec, settings.assign_approval_ttl_sec)
        self.assignments = AssignmentService(self.uow, self.inventory, policies, self.clock, self.metrics)
        self.vehicles = VehicleService(self.uow, self.inventory, self.clock)
        self.trips = TripService(self.uow)
        self.seed = SeedService(self.uow, settings.seed_path)

        self.expiry_worker = AssignmentExpiryWorker(self.assignments)
        self.retry_worker = DecisionRetryWorker(self.assignments)
        self._scheduler = WorkerScheduler([self.expiry_worker, self.retry_worker], settings.scheduler_interval_sec)
        self.metrics.watch_vehicles(self._count_vehicles)

    def start(self, run_workers: bool) -> None:
        self.database.init_schema()
        self.seed.load()
        if run_workers:
            self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.stop()
        if isinstance(self.inventory, InventoryClient):
            self.inventory.close()

    def _count_vehicles(self) -> dict[str, int]:
        with self.uow.read() as uow:
            return uow.vehicles.count_by_status()
