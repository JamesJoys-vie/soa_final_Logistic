from fastapi import APIRouter, Header, Query, HTTPException, status
from typing import List, Optional
from app.services.request_service import RequestService
from app.schemas import (
    RequestCreate,
    RequestApprove,
    RequestReject,
    RequestSuspend,
    RequestResponse
)

router = APIRouter(prefix="/requests", tags=["Requests"])

def get_current_user_context(
    x_user_name: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
    """Lấy thông tin người dùng từ Header chuyển tiếp bởi Gateway hoặc giá trị mặc định cho demo/test"""
    username = x_user_name or "staff_demo"
    role = x_user_role or "MANAGER"
    return username, role

@router.post("", response_model=RequestResponse, summary="Nhân viên tạo yêu cầu xử lý mới (mặc định Chờ xử lý)")
def create_request(
    data: RequestCreate,
    x_user_name: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
    username, _ = get_current_user_context(x_user_name, x_user_role)
    return RequestService.create_request(data, username)

@router.get("", response_model=List[RequestResponse], summary="Xem danh sách yêu cầu (Nhân viên: của mình, Quản lý: tất cả)")
def get_requests(
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: PENDING, SUSPENDED, APPROVED, REJECTED"),
    type: Optional[str] = Query(None, description="Lọc theo loại: DAMAGED, SLOW_MOVING, NO_OUTBOUND, OTHER"),
    x_user_name: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
    username, role = get_current_user_context(x_user_name, x_user_role)
    return RequestService.get_requests(username, role, status_filter=status, type_filter=type)

@router.get("/{id}", response_model=RequestResponse, summary="Chi tiết yêu cầu và lịch sử thay đổi trạng thái")
def get_request_by_id(id: int):
    return RequestService.get_request_by_id(id)

@router.post("/{id}/suspend", response_model=RequestResponse, summary="Quản lý chuyển yêu cầu sang Treo (hạn 4 giờ)")
def suspend_request(
    id: int,
    data: Optional[RequestSuspend] = None,
    x_user_name: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
    username, role = get_current_user_context(x_user_name, x_user_role)
    if role != "MANAGER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Quản lý mới có quyền chuyển trạng thái Treo")
    return RequestService.suspend_request(id, username, data)

@router.post("/{id}/approve", response_model=RequestResponse, summary="Quản lý Chấp thuận yêu cầu (Bắt buộc kèm chỉ dẫn/lý do)")
def approve_request(
    id: int,
    data: RequestApprove,
    x_user_name: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
    username, role = get_current_user_context(x_user_name, x_user_role)
    if role != "MANAGER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Quản lý mới có quyền Chấp thuận yêu cầu")
    return RequestService.approve_request(id, username, data)

@router.post("/{id}/reject", response_model=RequestResponse, summary="Quản lý Từ chối yêu cầu (Bắt buộc kèm lý do)")
def reject_request(
    id: int,
    data: RequestReject,
    x_user_name: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
    username, role = get_current_user_context(x_user_name, x_user_role)
    if role != "MANAGER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Quản lý mới có quyền Từ chối yêu cầu")
    return RequestService.reject_request(id, username, data)
