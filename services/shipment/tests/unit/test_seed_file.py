"""seed.json shared with Inventory: consistency checks (a risk listed in section 8 of the plan).

Inventory (Hiệu) loads items[].initial_stock; Shipment loads vehicles and trips. Both parts must agree.
"""
import json

import pytest

from app.domain.enums import VehicleStatus
from tests.support import SEED_PATH

SEED = json.loads(SEED_PATH.read_text(encoding="utf-8"))
ITEMS = {item["id"]: item for item in SEED["items"]}
VEHICLES = {vehicle["id"]: vehicle for vehicle in SEED["vehicles"]}


def open_trips(direction: str) -> list[dict]:
    return [trip for trip in SEED["trips"] if trip["direction"] == direction and trip["closed_at"] is None]


def boxes_on(trips: list[dict], item_id: int) -> int:
    return sum(line["boxes"] for trip in trips for line in trip["lines"] if line["item_id"] == item_id)


@pytest.mark.parametrize("item_id", sorted(ITEMS))
def test_incoming_equals_open_inbound_trips(item_id):
    assert ITEMS[item_id]["initial_stock"]["incoming"] == boxes_on(open_trips("IN"), item_id)


@pytest.mark.parametrize("item_id", sorted(ITEMS))
def test_allocated_equals_outbound_trips_not_departed(item_id):
    assert ITEMS[item_id]["initial_stock"]["allocated"] == boxes_on(open_trips("OUT"), item_id)


def test_no_reservation_in_seed_because_nothing_is_pending():
    assert all(item["initial_stock"]["reserved"] == 0 for item in ITEMS.values())


def test_references_exist_and_boxes_positive():
    for trip in SEED["trips"]:
        assert trip["vehicle_id"] in VEHICLES
        assert {line["item_id"] for line in trip["lines"]} <= set(ITEMS)
        assert all(line["boxes"] > 0 for line in trip["lines"])


@pytest.mark.parametrize(("statuses", "direction"), [
    ({"ARRIVING", "WAITING_UNLOAD", "UNLOADING"}, "IN"), ({"WAITING_LOAD", "LOADING"}, "OUT")])
def test_each_vehicle_on_a_trip_has_exactly_one_open_trip(statuses, direction):
    carrying = sorted(trip["vehicle_id"] for trip in open_trips(direction))
    assert carrying == sorted(v["id"] for v in SEED["vehicles"] if v["status"] in statuses)


def test_every_status_is_valid_and_idle_vehicles_exist():
    statuses = {vehicle["status"] for vehicle in SEED["vehicles"]}
    assert "IDLE" in statuses and statuses <= {status.value for status in VehicleStatus}


def test_five_categories_of_the_assignment():
    assert {item["category"] for item in ITEMS.values()} == {
        "Quần áo", "Đồ điện tử", "Đồ gia dụng", "Văn phòng phẩm", "Nội thất"}
