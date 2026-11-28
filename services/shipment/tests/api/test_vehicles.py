"""Vehicle status and its effect on stock."""
import pytest

from tests.support import AUTHORIZED, MANAGER, auth


def move(client, vehicle_id, status, user=MANAGER):
    return client.patch(f"/vehicles/{vehicle_id}/status", json={"status": status}, headers=auth(user))


def status_of(client, vehicle_id):
    vehicles = client.get("/vehicles", headers=auth(MANAGER)).json()
    return next(v for v in vehicles if v["id"] == vehicle_id)["status"]


@pytest.mark.parametrize("user", [MANAGER, AUTHORIZED])
def test_list_shows_three_groups(client, user):
    vehicles = client.get("/vehicles", headers=auth(user)).json()
    assert len(vehicles) == 12
    assert {v["group"] for v in vehicles} == {"INBOUND", "IDLE", "OUTBOUND"}


def test_filter_by_one_or_many_statuses(client):
    def ids(*statuses):
        return [v["id"] for v in client.get("/vehicles", params={"status": statuses}, headers=auth(MANAGER)).json()]

    assert ids("IDLE") == [5, 6, 7, 8]
    assert ids("ARRIVING", "WAITING_UNLOAD", "UNLOADING") == [1, 2, 3, 4]


def test_unloading_increases_stock_immediately(client, inventory):
    on_hand, incoming = inventory.on_hand[1], inventory.incoming[1]
    assert move(client, 1, "WAITING_UNLOAD").status_code == 200
    assert move(client, 1, "UNLOADING").status_code == 200
    assert inventory.on_hand[1] == on_hand              # no increase before unloading is finished
    assert move(client, 1, "IDLE").json()["status"] == "IDLE"
    assert inventory.on_hand[1] == on_hand + 50         # trip 1 carries 50 boxes of item 1
    assert inventory.incoming[1] == incoming - 50
    assert client.get("/trips/1", headers=auth(MANAGER)).json()["closed_at"] is not None


def test_every_move_is_written_to_history(client, container):
    move(client, 1, "WAITING_UNLOAD", AUTHORIZED)
    with container.database.read() as conn:
        rows = [tuple(r) for r in conn.execute(
            "SELECT vehicle_id, from_status, to_status, changed_by FROM vehicle_status_history")]
    assert rows == [(1, "ARRIVING", "WAITING_UNLOAD", "2")]


@pytest.mark.parametrize(("vehicle_id", "target"), [
    (1, "IDLE"),           # skips a step
    (5, "WAITING_LOAD"),   # only the system does this when an assignment takes effect
    (11, "ARRIVING"),      # already departed
    (3, "ARRIVING"),       # goes backwards
])
def test_invalid_transition_is_409(client, vehicle_id, target):
    response = move(client, vehicle_id, target)
    assert (response.status_code, response.json()["code"]) == (409, "INVALID_TRANSITION")


def test_inventory_down_keeps_vehicle_and_stock(client, inventory):
    inventory.is_down = True
    assert move(client, 4, "IDLE").status_code == 502
    assert status_of(client, 4) == "UNLOADING"
    inventory.is_down = False
    on_hand = inventory.on_hand[9]
    assert move(client, 4, "IDLE").status_code == 200
    assert inventory.on_hand[9] == on_hand + 25         # a retry adds the stock only once


def test_departure_of_a_seeded_outbound_trip(client, inventory):
    """Outbound trip from the seed (vehicle 10 LOADING): departure subtracts exactly the lines of trip 8."""
    on_hand, allocated = inventory.on_hand[7], inventory.allocated[7]
    assert move(client, 10, "DEPARTED").status_code == 200
    assert (inventory.on_hand[7], inventory.allocated[7]) == (on_hand - 60, allocated - 60)


def test_unknown_vehicle_and_bad_input(client):
    assert move(client, 999, "IDLE").status_code == 404
    assert move(client, 1, "FLYING").status_code == 400
    assert move(client, 2**70, "IDLE").status_code == 400
