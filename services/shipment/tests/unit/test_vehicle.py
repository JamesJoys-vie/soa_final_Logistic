"""Vehicle state machine: 7 states, 3 groups, exactly one step at a time."""
import itertools

import pytest

from app.core.errors import Conflict
from app.domain.enums import VehicleGroup, VehicleStatus
from app.domain.vehicle import Vehicle

S = VehicleStatus
ALLOWED = {(S.ARRIVING, S.WAITING_UNLOAD), (S.WAITING_UNLOAD, S.UNLOADING), (S.UNLOADING, S.IDLE),
           (S.WAITING_LOAD, S.LOADING), (S.LOADING, S.DEPARTED)}


def vehicle(status: VehicleStatus) -> Vehicle:
    return Vehicle(1, "51C-123.45", "Tài xế", status)


@pytest.mark.parametrize(("source", "target"), list(itertools.product(S, S)))
def test_only_the_five_manual_steps_are_allowed(source, target):
    if (source, target) in ALLOWED:
        vehicle(source).ensure_can_move_to(target)
    else:
        with pytest.raises(Conflict) as error:
            vehicle(source).ensure_can_move_to(target)
        assert error.value.code == "INVALID_TRANSITION"


def test_seven_statuses_in_three_groups():
    groups = {status: vehicle(status).group for status in S}
    assert len(groups) == 7
    assert [s for s, g in groups.items() if g == VehicleGroup.INBOUND] == [S.ARRIVING, S.WAITING_UNLOAD, S.UNLOADING]
    assert [s for s, g in groups.items() if g == VehicleGroup.IDLE] == [S.IDLE]
    assert [s for s, g in groups.items() if g == VehicleGroup.OUTBOUND] == [S.WAITING_LOAD, S.LOADING, S.DEPARTED]


@pytest.mark.parametrize("status", [s for s in S if s != S.IDLE])
def test_only_idle_vehicle_is_assignable(status):
    vehicle(S.IDLE).ensure_assignable()
    with pytest.raises(Conflict):
        vehicle(status).ensure_assignable()
