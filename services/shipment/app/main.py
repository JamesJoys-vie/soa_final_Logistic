"""Shipment service. Author: Phan Huy Bính (524H0081). Run: uvicorn app.main:create_app --factory"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.container import Container
from app.core.config import Settings
from app.core.error_handlers import install_error_handlers
from app.core.logging import setup_logging
from app.core.request_context import RequestIdMiddleware
from app.routers import assignments, system, trips, vehicles


def create_app(container: Container | None = None, *, run_workers: bool = True) -> FastAPI:
    setup_logging()
    container = container or Container(Settings.from_env())

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        container.start(run_workers)
        yield
        container.stop()

    app = FastAPI(title="Shipment Service", version="1.0.0", lifespan=lifespan,
                  description="Xe, lượt xe đến/đi và lần gán hàng xuất kho (xác nhận 30 giây, duyệt 2 phút).")
    app.state.container = container
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)
    for module in (vehicles, trips, assignments, system):
        app.include_router(module.router)

    instrumentator = Instrumentator(excluded_handlers=["/metrics", "/health"], registry=container.metrics.registry)
    instrumentator.instrument(app).expose(app, include_in_schema=False)

    for operations in app.openapi()["paths"].values():  # invalid input returns 400, not FastAPI's default 422
        for operation in operations.values():
            operation["responses"].pop("422", None)
    return app
