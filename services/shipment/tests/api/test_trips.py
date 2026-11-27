"""Inbound / outbound trips and the goods on each trip."""
from tests.support import MANAGER, auth


def test_filter_by_direction(client):
    def directions(**params):
        return {t["direction"] for t in client.get("/trips", params=params, headers=auth(MANAGER)).json()}

    assert directions(direction="IN") == {"IN"}
    assert directions(direction="OUT") == {"OUT"}
    assert directions() == {"IN", "OUT"}


def test_detail_has_lines(client):
    trip = client.get("/trips/1", headers=auth(MANAGER)).json()
    assert trip["plate"] == "51C-123.45"
    assert trip["lines"] == [{"item_id": 1, "boxes": 50}, {"item_id": 5, "boxes": 100}, {"item_id": 7, "boxes": 150}]


def test_unknown_trip_and_bad_direction(client):
    assert client.get("/trips/999", headers=auth(MANAGER)).status_code == 404
    assert client.get("/trips", params={"direction": "UP"}, headers=auth(MANAGER)).status_code == 400
