from fastapi import APIRouter

from app.domain.enums import TripDirection
from app.routers.deps import ContainerDep, Manager
from app.routers.responses import errors
from app.schemas.common import PositiveInt
from app.schemas.trip import TripOut

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("", response_model=list[TripOut], responses=errors(), summary="Lượt xe đến (IN) / đi (OUT) và hàng hóa")
def list_trips(container: ContainerDep, _: Manager, direction: TripDirection | None = None):
    return container.trips.find(direction)


@router.get("/{trip_id}", response_model=TripOut, responses=errors(404), summary="Chi tiết một lượt xe")
def get_trip(trip_id: PositiveInt, container: ContainerDep, _: Manager):
    return container.trips.get(trip_id)
