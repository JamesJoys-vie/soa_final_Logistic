from fastapi import APIRouter, Header, HTTPException, status
from app.config import settings
from app.services.inventory_service import InventoryService
from app.schemas import (
    ReservationCreateRequest,
    ReservationResponse,
    TripReceiptRequest,
    TripDepartureRequest,
    AdjustmentRequest
)

router = APIRouter(prefix="/internal", tags=["Internal APIs (Shipment & Request Calls)"])

def verify_internal_key(x_internal_key: str = Header(None)):
    """Xác thực khóa bảo mật giữa các microservices nội bộ"""
    if not x_internal_key or x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "UNAUTHORIZED_SERVICE", "message": "Truy cập API nội bộ bị từ chối: Khóa dịch vụ không hợp lệ"}
        )

@router.post("/reservations", response_model=ReservationResponse, summary="Giữ chỗ hàng trọn gói cho lần gán")
def create_reservation(data: ReservationCreateRequest, x_internal_key: str = Header(None)):
    verify_internal_key(x_internal_key)
    return InventoryService.create_reservation(data)

@router.post("/reservations/{assignment_id}/commit", summary="Chốt giữ chỗ: reserved chuyển sang allocated")
def commit_reservation(assignment_id: str, x_internal_key: str = Header(None)):
    verify_internal_key(x_internal_key)
    return InventoryService.commit_reservation(assignment_id)

@router.post("/reservations/{assignment_id}/release", summary="Nhả giữ chỗ: hoàn lại reserved")
def release_reservation(assignment_id: str, x_internal_key: str = Header(None)):
    verify_internal_key(x_internal_key)
    return InventoryService.release_reservation(assignment_id)

@router.post("/receipts", summary="Xe lượt đến thả xong: incoming chuyển sang on_hand")
def process_receipt(data: TripReceiptRequest, x_internal_key: str = Header(None)):
    verify_internal_key(x_internal_key)
    return InventoryService.process_receipt(data)

@router.post("/departures", summary="Xe rời kho: trừ allocated và on_hand")
def process_departure(data: TripDepartureRequest, x_internal_key: str = Header(None)):
    verify_internal_key(x_internal_key)
    return InventoryService.process_departure(data)

@router.post("/adjustments", summary="Điều chỉnh tồn khi yêu cầu xử lý được Chấp thuận")
def process_adjustment(data: AdjustmentRequest, x_internal_key: str = Header(None)):
    verify_internal_key(x_internal_key)
    return InventoryService.process_adjustment(data)
