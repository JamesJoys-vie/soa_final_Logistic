"""Shipment business metrics from the plan's metric table. Each app has its own registry."""
from collections.abc import Callable, Iterator, Mapping

from prometheus_client import CollectorRegistry, Counter
from prometheus_client.core import GaugeMetricFamily


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self._assignments = Counter("assignments_total", "Số lần gán theo trạng thái", ["status"],
                                    registry=self.registry)
        self._upstream_errors = Counter("inter_service_errors_total", "Số lỗi khi gọi service khác", ["target"],
                                        registry=self.registry)

    def assignment_entered(self, status: str) -> None:
        self._assignments.labels(status=status).inc()

    def upstream_failed(self, target: str) -> None:
        self._upstream_errors.labels(target=target).inc()

    def watch_vehicles(self, count_by_status: Callable[[], Mapping[str, int]]) -> None:
        self.registry.register(_VehiclesByStatus(count_by_status))


class _VehiclesByStatus:
    """Gauge counted in the database at scrape time, so it stays correct after a restart."""

    def __init__(self, count_by_status: Callable[[], Mapping[str, int]]):
        self._count_by_status = count_by_status

    def describe(self) -> list[GaugeMetricFamily]:  # static: no database yet at registration
        return [self._family()]

    def collect(self) -> Iterator[GaugeMetricFamily]:
        gauge = self._family()
        for status, count in self._count_by_status().items():
            gauge.add_metric([status], count)
        yield gauge

    @staticmethod
    def _family() -> GaugeMetricFamily:
        return GaugeMetricFamily("vehicles_by_status", "Số xe theo trạng thái", labels=["status"])
