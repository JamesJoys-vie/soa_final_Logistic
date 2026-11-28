from fastapi import APIRouter

from app.domain.enums import AssignmentStatus
from app.routers.deps import AuthorizedStaff, ContainerDep, Manager, ManagerOrAuthorizedStaff
from app.routers.responses import errors
from app.schemas.assignment import AssignmentIn, AssignmentOut
from app.schemas.common import PositiveInt

router = APIRouter(prefix="/assignments", tags=["Assignments"])

_decision_errors = errors(404, 409, 502, 504)


@router.post("", response_model=AssignmentOut, status_code=201, responses=errors(404, 409, 502, 504),
             summary="Tạo lần gán và giữ chỗ trọn gói (hạn 30 giây hoặc 2 phút theo vai trò)")
def create_assignment(body: AssignmentIn, container: ContainerDep, user: ManagerOrAuthorizedStaff):
    assignment = container.assignments.create(user, body.vehicle_id, body.destination, body.to_lines())
    return AssignmentOut.of(assignment, container.clock.now_iso())


@router.get("", response_model=list[AssignmentOut], responses=errors(),
            summary="Quản lý: tất cả (hộp thư duyệt). Nhân viên có thẩm quyền: của mình")
def list_assignments(container: ContainerDep, user: ManagerOrAuthorizedStaff, status: AssignmentStatus | None = None):
    found = container.assignments.find(user, status)
    return [AssignmentOut.of(assignment, container.clock.now_iso()) for assignment in found]


@router.post("/{assignment_id}/confirm", response_model=AssignmentOut, responses=_decision_errors,
             summary="Quản lý xác nhận hoặc chấp thuận")
def confirm(assignment_id: PositiveInt, container: ContainerDep, user: Manager):
    return AssignmentOut.of(container.assignments.confirm(user, assignment_id), container.clock.now_iso())


@router.post("/{assignment_id}/reject", response_model=AssignmentOut, responses=_decision_errors,
             summary="Quản lý từ chối")
def reject(assignment_id: PositiveInt, container: ContainerDep, user: Manager):
    return AssignmentOut.of(container.assignments.reject(user, assignment_id), container.clock.now_iso())


@router.post("/{assignment_id}/withdraw", response_model=AssignmentOut, responses=_decision_errors,
             summary="Nhân viên có thẩm quyền rút lần gán của mình")
def withdraw(assignment_id: PositiveInt, container: ContainerDep, user: AuthorizedStaff):
    return AssignmentOut.of(container.assignments.withdraw(user, assignment_id), container.clock.now_iso())
