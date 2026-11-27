from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.routers.deps import ContainerDep

router = APIRouter(tags=["System"])


@router.get("/health", summary="Kiểm tra sức khỏe (Docker healthcheck)")
def health(container: ContainerDep):
    ok = container.database.is_up()
    return JSONResponse({"status": "ok" if ok else "error", "service": "shipment"}, status_code=200 if ok else 503)
