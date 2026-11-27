"""401, 403 and the shared error shape."""
import time

import pytest

from tests.support import AUTHORIZED, MANAGER, STAFF, auth, make_token

ENDPOINTS = [
    ("GET", "/vehicles"), ("PATCH", "/vehicles/1/status"), ("GET", "/trips"), ("GET", "/trips/1"),
    ("GET", "/assignments"), ("POST", "/assignments"), ("POST", "/assignments/1/confirm"),
    ("POST", "/assignments/1/reject"), ("POST", "/assignments/1/withdraw"),
]
BODY = {"vehicle_id": 5, "destination": "Q3", "status": "IDLE", "lines": [{"item_id": 1, "boxes": 1}]}


@pytest.mark.parametrize(("method", "path"), ENDPOINTS)
def test_every_endpoint_needs_a_token(client, method, path):
    response = client.request(method, path, json=BODY)
    assert response.status_code == 401
    assert set(response.json()) == {"code", "message", "details"}


@pytest.mark.parametrize(("method", "path"), ENDPOINTS)
def test_plain_staff_has_no_access_to_shipment(client, method, path):
    assert client.request(method, path, json=BODY, headers=auth(STAFF)).status_code == 403


@pytest.mark.parametrize(("method", "path"), [
    ("GET", "/trips"), ("GET", "/trips/1"), ("POST", "/assignments/1/confirm"), ("POST", "/assignments/1/reject")])
def test_manager_only(client, method, path):
    assert client.request(method, path, headers=auth(AUTHORIZED)).status_code == 403


def test_withdraw_is_not_for_manager(client):
    assert client.post("/assignments/1/withdraw", headers=auth(MANAGER)).status_code == 403


@pytest.mark.parametrize(("token", "code"), [
    ("abc.def.ghi", "INVALID_TOKEN"),
    (make_token(MANAGER, secret="another-secret-key-with-32-bytes-or-more"), "INVALID_TOKEN"),
    (make_token(MANAGER, role="ADMIN"), "INVALID_TOKEN"),
    (make_token(MANAGER, role=None), "INVALID_TOKEN"),
    (make_token(MANAGER, exp=None), "INVALID_TOKEN"),
    (make_token(MANAGER, exp=int(time.time()) - 1), "TOKEN_EXPIRED"),
])
def test_bad_tokens(client, token, code):
    response = client.get("/vehicles", headers={"Authorization": f"Bearer {token}"})
    assert (response.status_code, response.json()["code"]) == (401, code)


def test_unknown_route_uses_the_common_error_shape(client):
    response = client.get("/internal/anything")
    assert response.status_code == 404 and set(response.json()) == {"code", "message", "details"}
