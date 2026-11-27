"""Base class for background jobs. Subclasses only implement run_once()."""
import logging
from abc import ABC, abstractmethod

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.request_context import request_id_scope

log = logging.getLogger("shipment.workers")


class PeriodicWorker(ABC):
    name = "worker"

    @abstractmethod
    def run_once(self) -> int:
        """Run one pass and return how many items were handled."""

    def tick(self) -> None:
        with request_id_scope():  # each pass gets its own trace id
            try:
                self.run_once()
            except Exception:     # one failed pass must not kill the worker
                log.exception("%s failed", self.name)


class WorkerScheduler:
    def __init__(self, workers: list[PeriodicWorker], interval_sec: float):
        self._scheduler = BackgroundScheduler(job_defaults={"coalesce": True, "max_instances": 1}, timezone="UTC")
        for worker in workers:
            self._scheduler.add_job(worker.tick, "interval", seconds=interval_sec, id=worker.name)

    def start(self) -> None:
        self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
