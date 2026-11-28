"""Wraps FakeInventory in a REST API shaped like Hiệu's real Inventory, to try out Shipment.

uvicorn dev.fake_inventory_api:create_app --factory --port 8002
When the real Inventory (branch Hieu) is available, use it instead.
"""
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.core.errors import AppError
from app.domain.line_item import LineItem
from dev.fake_inventory import FakeInventory


class Line(BaseModel):
    item_id: int
    boxes: int


class ReservationIn(BaseModel):
    assignment_id: str
    lines: list[Line]


class TripIn(BaseModel):
    trip_id: str
    lines: list[Line]


def create_app(store: FakeInventory | None = None, internal_api_key: str | None = None) -> FastAPI:
    store = store or FakeInventory.from_seed(os.environ["SEED_PATH"])
    key = internal_api_key or os.environ["INTERNAL_API_KEY"]
    app = FastAPI(title="Fake Inventory (dev only)")

    def call(x_internal_key: str | None, action, *args):
        if x_internal_key != key:      # the real Inventory returns 403 for a wrong internal key
            raise HTTPException(403, detail={"code": "UNAUTHORIZED_SERVICE", "message": "Khóa dịch vụ không hợp lệ"})
        try:
            action(*args)
        except AppError as exc:        # the real Inventory uses HTTPException, so errors sit in "detail"
            raise HTTPException(exc.status_code, detail=exc.body()) from exc

    def lines_of(lines: list[Line]) -> list[LineItem]:
        return [LineItem(line.item_id, line.boxes) for line in lines]

    @app.post("/internal/reservations")
    def reserve(body: ReservationIn, x_internal_key: str | None = Header(None)):
        call(x_internal_key, store.reserve, int(body.assignment_id), lines_of(body.lines))
        return {"assignment_id": body.assignment_id, "status": "ACTIVE"}

    @app.post("/internal/reservations/{assignment_id}/commit")
    def commit(assignment_id: str, x_internal_key: str | None = Header(None)):
        call(x_internal_key, store.commit, int(assignment_id))
        return {"assignment_id": assignment_id, "status": "COMMITTED"}

    @app.post("/internal/reservations/{assignment_id}/release")
    def release(assignment_id: str, x_internal_key: str | None = Header(None)):
        if store.status_of(int(assignment_id)) is None and x_internal_key == key:
            raise HTTPException(404, detail={"code": "RESERVATION_NOT_FOUND", "message": "Không tìm thấy giữ chỗ"})
        call(x_internal_key, store.release, int(assignment_id))
        return {"assignment_id": assignment_id, "status": "RELEASED"}

    @app.post("/internal/receipts")
    def receipts(body: TripIn, x_internal_key: str | None = Header(None)):
        call(x_internal_key, store.receive, int(body.trip_id), lines_of(body.lines))
        return {"trip_id": body.trip_id}

    @app.post("/internal/departures")
    def departures(body: TripIn, x_internal_key: str | None = Header(None)):
        call(x_internal_key, store.depart, int(body.trip_id), lines_of(body.lines))
        return {"trip_id": body.trip_id}

    @app.get("/items")
    def items():
        return [{name: item[name] for name in ("id", "sku", "name", "category", "unit")} for item in store.items]

    @app.get("/stock")
    def stock():
        return [{"item_id": i, "on_hand": store.on_hand[i], "incoming": store.incoming[i],
                 "allocated": store.allocated[i], "reserved": store.reserved[i]} for i in store.on_hand]

    return app
