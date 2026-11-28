"""Assignments: reservation, 30-second / 2-minute deadlines, five states, 409 on races."""
import pytest

from tests.support import AUTHORIZED, MANAGER, OTHER_AUTHORIZED, auth

LINES = [{"item_id": 3, "boxes": 50}, {"item_id": 1, "boxes": 100}]


def create(client, user=MANAGER, vehicle_id=5, lines=LINES, destination="Phường 7, Quận 3"):
    return client.post("/assignments", headers=auth(user),
                       json={"vehicle_id": vehicle_id, "destination": destination, "lines": lines})


def act(client, assignment, action, user=MANAGER):
    return client.post(f"/assignments/{assignment['id']}/{action}", headers=auth(user))


def find(client, assignment_id, user=MANAGER):
    found = client.get("/assignments", headers=auth(user)).json()
    return next((a for a in found if a["id"] == assignment_id), None)


def vehicle(client, vehicle_id=5):
    vehicles = client.get("/vehicles", headers=auth(MANAGER)).json()
    return next(v for v in vehicles if v["id"] == vehicle_id)


# ---- create ---------------------------------------------------------------------------
@pytest.mark.parametrize(("user", "expires_at"), [
    (MANAGER, "2026-11-25T08:00:30.000000Z"), (AUTHORIZED, "2026-11-25T08:02:00.000000Z")])
def test_create_reserves_locks_vehicle_and_starts_clock(client, inventory, user, expires_at):
    response = create(client, user)
    assert response.status_code == 201
    assignment = response.json()
    assert assignment["status"] == "PENDING" and assignment["decision"] is None
    assert assignment["expires_at"] == expires_at
    assert assignment["server_time"] == "2026-11-25T08:00:00.000000Z"
    assert (inventory.reserved[1], inventory.reserved[3]) == (100, 50)
    assert vehicle(client)["pending_assignment_id"] == assignment["id"]
    assert vehicle(client)["status"] == "IDLE"          # no new vehicle state is added


@pytest.mark.parametrize("change", [
    {"lines": []}, {"destination": "   "}, {"lines": [{"item_id": 1, "boxes": 0}]},
    {"lines": [{"item_id": 1, "boxes": 5}, {"item_id": 1, "boxes": 5}]}, {"lines": [{"item_id": 1, "boxes": 2**70}]}])
def test_bad_input_is_400(client, change):
    assert create(client, **change).status_code == 400


def test_unknown_vehicle_is_404_and_busy_vehicle_is_409(client):
    assert create(client, vehicle_id=999).status_code == 404
    response = create(client, vehicle_id=1)
    assert (response.status_code, response.json()["code"]) == (409, "VEHICLE_NOT_IDLE")


def test_one_pending_assignment_per_vehicle(client):
    create(client)
    response = create(client, AUTHORIZED, lines=[{"item_id": 8, "boxes": 1}])
    assert (response.status_code, response.json()["code"]) == (409, "VEHICLE_LOCKED")


def test_one_short_line_rejects_the_whole_assignment(client, inventory):
    response = create(client, lines=[{"item_id": 1, "boxes": 10}, {"item_id": 4, "boxes": 61}])
    assert (response.status_code, response.json()["code"]) == (409, "STOCK_INSUFFICIENT")
    assert response.json()["details"] == [{"item_id": 4, "requested": 61, "available": 50, "missing": 11}]
    assert inventory.reserved[1] == 0
    assert client.get("/assignments", headers=auth(MANAGER)).json() == []
    assert vehicle(client)["pending_assignment_id"] is None


def test_overlapping_assignments_on_two_vehicles(client):
    create(client, vehicle_id=5, lines=[{"item_id": 4, "boxes": 50}])
    response = create(client, AUTHORIZED, vehicle_id=6, lines=[{"item_id": 4, "boxes": 20}])
    assert response.status_code == 409
    assert response.json()["details"] == [{"item_id": 4, "requested": 20, "available": 0, "missing": 20}]


def test_stock_is_checked_on_hand_not_projected(client):
    """Item 4: available 60 - 10 = 50, projected 60 + 40 - 10 = 90. Assigning 70 must be refused."""
    assert create(client, lines=[{"item_id": 4, "boxes": 70}]).status_code == 409


def test_assignment_ids_are_never_reused(client):
    first = create(client).json()["id"]
    act(client, {"id": first}, "reject")
    create(client, lines=[{"item_id": 4, "boxes": 999}])    # 409, the record is deleted
    assert create(client).json()["id"] == first + 2         # the id is Inventory's idempotency key


# ---- manager -----------------------------------------------------------------------
def test_manager_confirms(client, inventory):
    assignment = create(client).json()
    confirmed = act(client, assignment, "confirm").json()
    assert confirmed["status"] == "CONFIRMED" and confirmed["approval_type"] == "MANUAL"
    assert confirmed["decided_by"] == confirmed["responsible_user"] == "1"
    assert inventory.status_of(assignment["id"]) == "COMMITTED"
    assert vehicle(client)["status"] == "WAITING_LOAD"
    trips = client.get("/trips", params={"direction": "OUT"}, headers=auth(MANAGER)).json()
    trip = next(t for t in trips if t["assignment_id"] == assignment["id"])
    assert trip["destination"] == "Phường 7, Quận 3" and trip["closed_at"] is None
    assert trip["lines"] == sorted(LINES, key=lambda line: line["item_id"])


def test_manager_rejects(client, inventory):
    assignment = create(client).json()
    rejected = act(client, assignment, "reject").json()
    assert rejected["status"] == "REJECTED" and rejected["approval_type"] is None
    assert inventory.status_of(assignment["id"]) == "RELEASED" and inventory.reserved[1] == 0
    assert vehicle(client)["status"] == "IDLE"
    assert create(client).status_code == 201                # vehicle unlocked, can be assigned again


def test_manager_silent_for_30_seconds_means_rejected(client, container, clock, inventory):
    assignment = create(client).json()
    clock.advance(29.9)
    assert container.expiry_worker.run_once() == 0
    clock.advance(0.1)
    assert container.expiry_worker.run_once() == 1
    expired = find(client, assignment["id"])
    assert expired["status"] == "REJECTED"
    assert (expired["decided_by"], expired["approval_type"], expired["responsible_user"]) == (None, None, None)
    assert inventory.status_of(assignment["id"]) == "RELEASED"
    assert vehicle(client)["pending_assignment_id"] is None


# ---- authorized staff ---------------------------------------------------------
def test_approval_inbox_then_manager_approves(client):
    assignment = create(client, AUTHORIZED).json()
    inbox = client.get("/assignments", params={"status": "PENDING"}, headers=auth(MANAGER)).json()
    assert [(a["id"], a["creator_role"]) for a in inbox] == [(assignment["id"], "AUTHORIZED_STAFF")]
    approved = act(client, assignment, "confirm").json()
    assert (approved["status"], approved["responsible_user"]) == ("CONFIRMED", "1")


def test_manager_silent_for_2_minutes_means_auto_approved(client, container, clock, inventory):
    assignment = create(client, AUTHORIZED).json()
    clock.advance(119.9)
    assert container.expiry_worker.run_once() == 0
    clock.advance(0.1)
    container.expiry_worker.run_once()
    approved = find(client, assignment["id"])
    assert approved["status"] == "AUTO_APPROVED"
    assert approved["decided_by"] is None                   # approver left empty
    assert approved["approval_type"] == "TIMEOUT"           # approval type: timeout
    assert approved["responsible_user"] == "2"              # responsible: the creator
    assert inventory.status_of(assignment["id"]) == "COMMITTED"
    assert vehicle(client)["status"] == "WAITING_LOAD"


def test_staff_withdraws(client, inventory):
    assignment = create(client, AUTHORIZED).json()
    assert act(client, assignment, "withdraw", AUTHORIZED).json()["status"] == "WITHDRAWN"
    assert inventory.status_of(assignment["id"]) == "RELEASED"


def test_withdraw_only_by_the_creator(client):
    own = create(client, AUTHORIZED).json()
    by_manager = create(client, vehicle_id=6, lines=[{"item_id": 8, "boxes": 1}]).json()
    assert act(client, own, "withdraw", OTHER_AUTHORIZED).status_code == 403
    assert act(client, by_manager, "withdraw", AUTHORIZED).status_code == 403


def test_staff_sees_only_own_assignments(client):
    own = create(client, AUTHORIZED).json()
    by_manager = create(client, vehicle_id=6, lines=[{"item_id": 8, "boxes": 1}]).json()
    assert find(client, own["id"], AUTHORIZED) and not find(client, by_manager["id"], AUTHORIZED)


# ---- late caller gets 409 -------------------------------------------------------------
@pytest.mark.parametrize("first", ["confirm", "reject"])
@pytest.mark.parametrize("second", ["confirm", "reject"])
def test_second_decision_is_409(client, first, second):
    assignment = create(client).json()
    act(client, assignment, first)
    response = act(client, assignment, second)
    assert (response.status_code, response.json()["code"]) == (409, "ASSIGNMENT_ALREADY_DECIDED")


def test_confirm_after_withdraw_is_409(client):
    assignment = create(client, AUTHORIZED).json()
    act(client, assignment, "withdraw", AUTHORIZED)
    response = act(client, assignment, "confirm")
    assert response.status_code == 409 and response.json()["details"]["status"] == "WITHDRAWN"


def test_deadline_is_exact_even_if_the_worker_has_not_run(client, clock):
    assignment = create(client).json()
    clock.advance(30)
    response = act(client, assignment, "confirm")
    assert (response.status_code, response.json()["code"]) == (409, "ASSIGNMENT_EXPIRED")


def test_unknown_assignment_is_404(client):
    assert act(client, {"id": 999}, "confirm").status_code == 404
    assert act(client, {"id": 999}, "withdraw", AUTHORIZED).status_code == 404


# ---- departure ----------------------------------------------------------------------------
def test_departure_decreases_stock_immediately(client, inventory):
    assignment = create(client).json()
    act(client, assignment, "confirm")
    on_hand = inventory.on_hand[1]
    for status in ("LOADING", "DEPARTED"):
        assert inventory.on_hand[1] == on_hand              # not subtracted before departure
        client.patch("/vehicles/5/status", json={"status": status}, headers=auth(AUTHORIZED))
    assert (inventory.on_hand[1], inventory.allocated[1]) == (on_hand - 100, 20)   # 20 from trip 7 in the seed
    assert vehicle(client)["status"] == "DEPARTED"
