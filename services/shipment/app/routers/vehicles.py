from typing import Annotated

from fastapi import APIRouter, Query

from app.domain.enums import VehicleStatus
from app.routers.deps import ContainerDep, ManagerOrAuthorizedStaff
from app.routers.responses import errors
from app.schemas.common import PositiveInt
from app.schemas.vehicle import VehicleOut, VehicleStatusIn

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=list[VehicleOut], responses=errors(),
            summary="Trạng thái xe (group là một trong ba nhóm hiển thị)")
def list_vehicles(container: ContainerDep, _: ManagerOrAuthorizedStaff,
                  status: Annotated[list[VehicleStatus] | None, Query(description="Lặp lại được")] = None):
    return [VehicleOut.of(vehicle, pending_id) for vehicle, pending_id in container.vehicles.find(status)]


@router.patch("/{vehicle_id}/status", response_model=VehicleOut, responses=errors(404, 409, 502, 504),
              summary="Chuyển trạng thái hợp lệ (thả xong: nhập tồn; rời kho: xuất tồn)")
def change_status(vehicle_id: PositiveInt, body: VehicleStatusIn, container: ContainerDep,
                  user: ManagerOrAuthorizedStaff):
    return VehicleOut.of(container.vehicles.change_status(user, vehicle_id, body.status))
