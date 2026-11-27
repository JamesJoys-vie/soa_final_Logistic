"""/health, /metrics, X-Request-Id, OpenAPI contract."""
import json

from tests.support import MANAGER, REPO_ROOT, auth

ASSIGNMENT = {"vehicle_id": 5, "destination": "Q3", "lines": [{"item_id": 1, "boxes": 1}]}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "shipment"}


def test_metrics_of_the_plan_are_exposed(client):
    created = client.post("/assignments", json=ASSIGNMENT, headers=auth(MANAGER)).json()
    client.post(f"/assignments/{created['id']}/confirm", headers=auth(MANAGER))
    text = client.get("/metrics").text
    for expected in ('vehicles_by_status{status="IDLE"} 3.0', 'vehicles_by_status{status="WAITING_LOAD"} 2.0',
                     'assignments_total{status="PENDING"} 1.0', 'assignments_total{status="CONFIRMED"} 1.0',
                     "# TYPE inter_service_errors_total counter", "# TYPE http_requests_total counter",
                     "# TYPE http_request_duration_seconds histogram"):
        assert expected in text


def test_request_id_is_kept_or_created(client):
    assert client.get("/health", headers={"X-Request-Id": "abc"}).headers["X-Request-Id"] == "abc"
    assert client.get("/health").headers["X-Request-Id"]


def operations(spec: dict) -> dict:
    return {f"{method} {path}": sorted(operation["responses"])
            for path, methods in spec["paths"].items() for method, operation in methods.items()}


def test_published_contract_is_up_to_date(client):
    """docs/shipment/openapi.json must match the code; regenerate with: python -m dev.export_openapi"""
    published = json.loads((REPO_ROOT / "docs" / "shipment" / "openapi.json").read_text(encoding="utf-8"))
    assert operations(published) == operations(client.get("/openapi.json").json())
    assert all("422" not in statuses for statuses in operations(published).values())    # invalid input returns 400
