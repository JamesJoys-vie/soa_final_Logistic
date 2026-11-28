"""Inventory failing half way: CONFIRMED only after a successful commit, no lost stock, no stuck vehicle."""
import pytest

from app.core.errors import Conflict, NotFound, UpstreamError, UpstreamTimeout
from app.domain.line_item import LineItem
from dev.fake_inventory import FakeInventory
from tests.support import AUTHORIZED, MANAGER

LINES = [LineItem(8, 10)]


def only(container):
    return container.assignments.find(MANAGER, None)[0]


@pytest.fixture
def pending(container):
    return container.assignments.create(AUTHORIZED, 5, "Q3", LINES)


def test_not_confirmed_until_inventory_commits(container, inventory, pending):
    inventory.is_down = True
    with pytest.raises(UpstreamError):
        container.assignments.confirm(MANAGER, pending.id)
    waiting = only(container)
    assert (waiting.status, waiting.decision) == ("PENDING", "CONFIRMED")
    assert container.trips.find("OUT") == [t for t in container.trips.find("OUT") if t.assignment_id is None]
    assert inventory.reserved[8] == 10                  # stock stays reserved, nobody else can take it

    assert container.retry_worker.run_once() == 0       # still down: not done, no crash
    inventory.is_down = False
    assert container.retry_worker.run_once() == 1
    assert only(container).status == "CONFIRMED" and inventory.status_of(pending.id) == "COMMITTED"
    assert container.retry_worker.run_once() == 0       # once done it is not called again


def test_nobody_can_overturn_a_decision_waiting_for_inventory(container, inventory, clock, pending):
    inventory.is_down = True
    with pytest.raises(UpstreamError):
        container.assignments.confirm(MANAGER, pending.id)
    with pytest.raises(Conflict):
        container.assignments.withdraw(AUTHORIZED, pending.id)
    clock.advance(500)
    assert container.expiry_worker.run_once() == 0
    with pytest.raises(Conflict):                       # vehicle still locked
        container.assignments.create(MANAGER, 5, "Q1", LINES)
    inventory.is_down = False
    container.retry_worker.run_once()
    assert only(container).status == "CONFIRMED"


@pytest.mark.parametrize(("action", "user", "status"), [("reject", MANAGER, "REJECTED"),
                                                        ("withdraw", AUTHORIZED, "WITHDRAWN")])
def test_release_is_retried_before_the_vehicle_is_unlocked(container, inventory, pending, action, user, status):
    inventory.is_down = True
    with pytest.raises(UpstreamError):
        getattr(container.assignments, action)(user, pending.id)
    assert only(container).status == "PENDING"
    inventory.is_down = False
    container.retry_worker.run_once()
    assert only(container).status == status and inventory.reserved[8] == 0


def test_timeout_decision_is_retried_too(container, inventory, clock, pending):
    inventory.is_down = True
    clock.advance(120)
    container.expiry_worker.run_once()
    assert (only(container).status, only(container).decision) == ("PENDING", "AUTO_APPROVED")
    inventory.is_down = False
    container.retry_worker.run_once()
    assert only(container).status == "AUTO_APPROVED" and only(container).responsible_user == "2"


def test_inventory_down_on_create_leaves_nothing_behind(container, inventory):
    inventory.is_down = True
    with pytest.raises(UpstreamError):
        container.assignments.create(MANAGER, 5, "Q3", LINES)
    assert container.assignments.find(MANAGER, None) == []          # users see no assignment
    inventory.is_down = False
    container.retry_worker.run_once()
    assert container.assignments.create(MANAGER, 5, "Q3", LINES).status == "PENDING"


class SlowInventory(FakeInventory):
    """The reservation succeeds but the response is lost: Shipment does not know the outcome."""

    def reserve(self, assignment_id, lines):
        super().reserve(assignment_id, lines)
        raise UpstreamTimeout("quá hạn", code="INVENTORY_TIMEOUT")


def test_reservation_with_lost_response_is_released(tmp_path, clock):
    from app.container import Container
    from tests.support import SEED_PATH, make_settings

    inventory = SlowInventory.from_seed(SEED_PATH)
    container = Container(make_settings(tmp_path), clock=clock, inventory=inventory)
    container.start(run_workers=False)
    with pytest.raises(UpstreamTimeout):
        container.assignments.create(MANAGER, 5, "Q3", LINES)
    assert inventory.reserved[8] == 10
    container.retry_worker.run_once()
    assert inventory.reserved[8] == 0


def crash_before_reservation(container, user=AUTHORIZED) -> int:
    with container.uow.transaction() as uow:
        return uow.assignments.add(vehicle_id=5, destination="Q3", creator=user,
                                   created_at=container.clock.now_iso(), lines=LINES)


def test_crash_before_reservation_is_never_auto_approved(container, clock):
    assignment_id = crash_before_reservation(container)
    with pytest.raises(NotFound):
        container.assignments.confirm(MANAGER, assignment_id)
    clock.advance(59)
    assert container.expiry_worker.run_once() == 0
    clock.advance(1)
    container.expiry_worker.run_once()
    container.retry_worker.run_once()
    assert container.assignments.find(MANAGER, None) == []
    assert container.assignments.create(MANAGER, 5, "Q3", LINES).status == "PENDING"     # vehicle unlocked


def test_worker_cancels_while_inventory_is_still_reserving(container, clock, inventory):
    """Once cancelled, it must not start its clock or become visible, even if Inventory just reserved."""
    original = inventory.reserve

    def slow_reserve(assignment_id, lines):
        clock.advance(61)
        container.expiry_worker.run_once()          # claims the cancellation, not released yet
        original(assignment_id, lines)

    inventory.reserve = slow_reserve
    with pytest.raises(UpstreamTimeout):
        container.assignments.create(AUTHORIZED, 5, "Q3", LINES)
    assert container.assignments.find(MANAGER, None) == [] and inventory.reserved[8] == 0
    container.retry_worker.run_once()
    inventory.reserve = original
    assert container.assignments.create(AUTHORIZED, 5, "Q3", LINES).status == "PENDING"


def test_late_reservation_is_released_even_if_inventory_forgot_the_release(container, clock, inventory):
    """Inventory reserves AFTER receiving the release and does not remember it: Shipment must release again."""
    original = inventory.reserve

    def slow_reserve(assignment_id, lines):
        clock.advance(61)
        container.expiry_worker.run_once()
        container.retry_worker.run_once()           # released, record deleted
        inventory.reservations.pop(assignment_id, None)  # real Inventory forgets releases of unknown ids
        original(assignment_id, lines)

    inventory.reserve = slow_reserve
    with pytest.raises(UpstreamTimeout):
        container.assignments.create(AUTHORIZED, 5, "Q3", LINES)
    assert inventory.reserved[8] == 0
