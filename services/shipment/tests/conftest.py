"""Shipment service tests. Author: Phan Huy Bính (524H0081)."""
import pytest
from fastapi.testclient import TestClient

from app.container import Container
from app.main import create_app
from dev.fake_inventory import FakeInventory
from tests.support import SEED_PATH, FakeClock, make_settings


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def inventory() -> FakeInventory:
    return FakeInventory.from_seed(SEED_PATH)


@pytest.fixture
def container(tmp_path, clock, inventory) -> Container:
    """One temporary SQLite file per test. Workers do not run in the background; tests call run_once()."""
    container = Container(make_settings(tmp_path), clock=clock, inventory=inventory)
    container.start(run_workers=False)
    return container


@pytest.fixture
def client(container):
    with TestClient(create_app(container, run_workers=False)) as client:
        yield client
