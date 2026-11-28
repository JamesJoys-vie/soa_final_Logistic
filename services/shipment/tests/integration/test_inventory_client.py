"""HTTP contract with Inventory: paths, internal key, X-Request-Id, 409 / 502 / 504, one retry."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.inventory_client import InventoryClient
from app.container import Container
from app.core.errors import Conflict, UpstreamError, UpstreamTimeout
from app.core.metrics import Metrics
from app.domain.line_item import LineItem
from app.main import create_app
from dev.fake_inventory import FakeInventory
from dev.fake_inventory_api import create_app as create_inventory_api
from tests.support import INTERNAL_KEY, MANAGER, SEED_PATH, FakeClock, auth, make_settings

LINES = [LineItem(3, 5), LineItem(1, 2)]


class Recorder:
    """Fakes Inventory at the HTTP level, records every request and returns the given answers in order."""

    def __init__(self, *answers):
        self.requests: list[httpx.Request] = []
        self._answers = list(answers)
        self.metrics = Metrics()
        transport = httpx.MockTransport(self._handle)
        self.client = InventoryClient(httpx.Client(transport=transport, base_url="http://inventory"),
                                      INTERNAL_KEY, self.metrics, retry_delay_sec=0)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        answer = self._answers.pop(0) if self._answers else httpx.Response(200, json={})
        if isinstance(answer, Exception):
            raise answer
        return answer

    @property
    def errors(self) -> float:
        return self.metrics.registry.get_sample_value("inter_service_errors_total", {"target": "inventory"}) or 0


@pytest.mark.parametrize(("call", "path", "body"), [
    (lambda c: c.reserve(7, LINES), "/internal/reservations",
     {"assignment_id": "7", "lines": [{"item_id": 1, "boxes": 2}, {"item_id": 3, "boxes": 5}]}),   # strings, by item_id
    (lambda c: c.commit(7), "/internal/reservations/7/commit", {}),
    (lambda c: c.release(7), "/internal/reservations/7/release", {}),
    (lambda c: c.receive(4, LINES), "/internal/receipts",
     {"trip_id": "4", "lines": [{"item_id": 1, "boxes": 2}, {"item_id": 3, "boxes": 5}]}),
    (lambda c: c.depart(8, LINES), "/internal/departures",
     {"trip_id": "8", "lines": [{"item_id": 1, "boxes": 2}, {"item_id": 3, "boxes": 5}]}),
])
def test_paths_bodies_and_key(call, path, body):
    recorder = Recorder()
    call(recorder.client)
    request, = recorder.requests
    assert (request.method, request.url.path, json.loads(request.content)) == ("POST", path, body)
    assert request.headers["X-Internal-Key"] == INTERNAL_KEY


def test_409_keeps_code_and_details_and_is_not_retried():
    details = [{"item_id": 1, "requested": 5, "available": 2, "missing": 3}]
    # the real Inventory uses FastAPI's HTTPException, so the error sits in "detail"
    body = {"detail": {"code": "STOCK_INSUFFICIENT", "message": "m", "details": details}}
    recorder = Recorder(httpx.Response(409, json=body))
    with pytest.raises(Conflict) as error:
        recorder.client.reserve(1, LINES)
    assert (error.value.code, error.value.details) == ("STOCK_INSUFFICIENT", details)
    assert len(recorder.requests) == 1 and recorder.errors == 0


@pytest.mark.parametrize(("answer", "error"), [
    (httpx.Response(503), UpstreamError), (httpx.ConnectError("refused"), UpstreamError),
    (httpx.Response(404), UpstreamError), (httpx.ReadTimeout("slow"), UpstreamTimeout)])
def test_failure_is_retried_once_then_reported(answer, error):
    recorder = Recorder(answer, answer)
    with pytest.raises(error):
        recorder.client.commit(1)
    assert len(recorder.requests) == 2 and recorder.errors == 1


def test_success_on_retry_is_not_an_error():
    recorder = Recorder(httpx.Response(500))
    recorder.client.commit(1)
    assert len(recorder.requests) == 2 and recorder.errors == 0


def test_request_id_travels_from_the_user_to_inventory(tmp_path):
    recorder = Recorder()
    container = Container(make_settings(tmp_path), clock=FakeClock(), inventory=recorder.client)
    with TestClient(create_app(container, run_workers=False)) as client:
        client.post("/assignments", headers={**auth(MANAGER), "X-Request-Id": "trace-1"},
                    json={"vehicle_id": 5, "destination": "Q3", "lines": [{"item_id": 1, "boxes": 1}]})
    assert [r.headers["X-Request-Id"] for r in recorder.requests] == ["trace-1"]


def test_504_reaches_the_user(tmp_path):
    recorder = Recorder(*[httpx.ReadTimeout("slow")] * 2)
    container = Container(make_settings(tmp_path), clock=FakeClock(), inventory=recorder.client)
    with TestClient(create_app(container, run_workers=False)) as client:
        response = client.patch("/vehicles/4/status", json={"status": "IDLE"}, headers=auth(MANAGER))
    assert (response.status_code, response.json()["code"]) == (504, "INVENTORY_TIMEOUT")


def test_release_of_a_reservation_that_never_existed_is_done():
    """The real Inventory returns 404 RESERVATION_NOT_FOUND: nothing to release, must not retry forever."""
    recorder = Recorder(httpx.Response(404, json={"detail": {"code": "RESERVATION_NOT_FOUND"}}))
    recorder.client.release(9)
    assert len(recorder.requests) == 1 and recorder.errors == 0


def test_fake_inventory_speaks_the_same_contract():
    store = FakeInventory.from_seed(SEED_PATH)
    http = TestClient(create_inventory_api(store, INTERNAL_KEY))
    client = InventoryClient(http, INTERNAL_KEY, Metrics(), retry_delay_sec=0)
    client.reserve(1, LINES)
    client.reserve(1, LINES)            # idempotent
    client.commit(1)
    client.commit(1)
    assert (store.reserved[1], store.allocated[1]) == (0, 22)
    client.depart(8, LINES)
    client.depart(8, LINES)
    assert (store.on_hand[1], store.allocated[1]) == (118, 20)
    client.release(99)                  # never reserved
    with pytest.raises(Conflict) as error:
        client.reserve(2, [LineItem(4, 61)])
    assert error.value.code == "STOCK_INSUFFICIENT"
    with pytest.raises(UpstreamError):  # wrong internal key: 403
        InventoryClient(http, "wrong", Metrics(), retry_delay_sec=0).commit(1)
