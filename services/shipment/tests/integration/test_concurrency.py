"""Real races with several threads: exactly ONE side wins and stock stays consistent."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from app.core.errors import AppError, Conflict
from app.domain.enums import VehicleStatus
from app.domain.line_item import LineItem
from tests.support import AUTHORIZED, MANAGER, OTHER_AUTHORIZED

LINES = [LineItem(8, 10)]


def race(*actions) -> list[str]:
    """Run the actions at the same time and return 'ok' or each side's error code."""
    barrier = Barrier(len(actions))

    def run(action):
        barrier.wait()
        try:
            action()
            return "ok"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(len(actions)) as pool:
        return list(pool.map(run, actions))


@pytest.mark.parametrize("_", range(15))
def test_confirm_and_withdraw_at_the_same_time(container, inventory, _):
    service = container.assignments
    assignment = service.create(AUTHORIZED, 5, "Q3", LINES)
    results = race(lambda: service.confirm(MANAGER, assignment.id), lambda: service.withdraw(AUTHORIZED, assignment.id))
    assert sorted(results) == ["ASSIGNMENT_ALREADY_DECIDED", "ok"]
    final = service.find(MANAGER, None)[0]
    confirmed = results[0] == "ok"
    assert final.status == ("CONFIRMED" if confirmed else "WITHDRAWN")
    assert inventory.status_of(assignment.id) == ("COMMITTED" if confirmed else "RELEASED")
    assert inventory.allocated[8] == (30 if confirmed else 20) and inventory.reserved[8] == 0


@pytest.mark.parametrize("user", [MANAGER, AUTHORIZED])
def test_many_workers_expire_the_same_assignment_once(container, clock, inventory, user):
    service = container.assignments
    assignment = service.create(user, 5, "Q3", LINES)
    clock.advance(120)
    counts = []
    race(*[lambda: counts.append(service.expire_due())] * 4)
    assert sum(counts) == 1
    assert inventory.status_of(assignment.id) == ("RELEASED" if user.is_manager else "COMMITTED")


def test_two_people_lock_the_same_vehicle(container):
    service = container.assignments
    results = race(lambda: service.create(AUTHORIZED, 6, "Q1", LINES),
                   lambda: service.create(OTHER_AUTHORIZED, 6, "Q1", LINES))
    assert sorted(results) == ["VEHICLE_LOCKED", "ok"]


def test_two_vehicles_compete_for_the_last_boxes(container, inventory):
    service, lines = container.assignments, [LineItem(10, 20)]      # item 10 has only 25 boxes available
    results = race(lambda: service.create(MANAGER, 5, "Q1", lines), lambda: service.create(AUTHORIZED, 6, "Q1", lines))
    assert sorted(results) == ["STOCK_INSUFFICIENT", "ok"]
    assert inventory.available(10) == 5


def test_two_people_finish_unloading_at_the_same_time(container, inventory):
    """The second user acts while the first is waiting for Inventory: both have passed the check."""
    on_hand, original, results = inventory.on_hand[9], inventory.receive, []

    def receive(trip_id, lines):
        original(trip_id, lines)
        if not results:
            results.append("second")
            container.vehicles.change_status(AUTHORIZED, 4, VehicleStatus.IDLE)

    inventory.receive = receive
    with pytest.raises(Conflict) as error:
        container.vehicles.change_status(MANAGER, 4, VehicleStatus.IDLE)
    assert error.value.code == "VEHICLE_STATUS_CHANGED"
    assert inventory.on_hand[9] == on_hand + 25                     # added only once
