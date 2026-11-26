from pydantic import BaseModel, Field
from typing import List, Optional, Any

# --- Items & Stock ---
class ItemResponse(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    unit: str

class StockDetailResponse(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    unit: str
    on_hand: int = Field(..., description="Tồn thực tế hiện có trong kho")
    incoming: int = Field(..., description="Hàng trên xe đến nhưng chưa hoàn thành thả hàng")
    allocated: int = Field(..., description="Hàng đã gán cho xe đi nhưng chưa rời kho")
    reserved: int = Field(..., description="Hàng đang giữ chỗ tạm thời (chờ duyệt/xác nhận)")
    projected_stock: int = Field(..., description="Tồn dự đoán = on_hand + incoming - allocated")
    available_stock: int = Field(..., description="Khả dụng = on_hand - allocated - reserved")

# --- Giữ chỗ (Reservations) ---
class ReservationLineCreate(BaseModel):
    item_id: int
    boxes: int = Field(..., gt=0, description="Số thùng cần giữ chỗ (lớn hơn 0)")

class ReservationCreateRequest(BaseModel):
    assignment_id: str = Field(..., description="Mã định danh lần gán hàng từ Shipment Service")
    lines: List[ReservationLineCreate] = Field(..., min_length=1, description="Danh sách các dòng hàng cần giữ chỗ trọn gói")

class MissingItemDetail(BaseModel):
    item_id: int
    requested: int
    available: int
    missing: int

class ReservationResponse(BaseModel):
    id: int
    assignment_id: str
    status: str
    created_at: str

# --- Nhập / Xuất kho (Receipts & Departures) ---
class TripLineItem(BaseModel):
    item_id: int
    boxes: int = Field(..., gt=0)

class TripReceiptRequest(BaseModel):
    trip_id: str = Field(..., description="Mã lượt xe đến hoàn thành dỡ hàng")
    lines: List[TripLineItem] = Field(..., min_length=1)

class TripDepartureRequest(BaseModel):
    trip_id: str = Field(..., description="Mã lượt xe xuất kho đã rời khỏi kho")
    lines: List[TripLineItem] = Field(..., min_length=1)

# --- Điều chỉnh tồn kho theo yêu cầu xử lý (Request Service) ---
class AdjustmentRequest(BaseModel):
    request_id: int = Field(..., description="ID của yêu cầu xử lý")
    item_id: int = Field(..., description="ID mặt hàng có vấn đề")
    action: str = Field(..., description="'DAMAGE_WRITE_OFF' hoặc 'FLAG'")
    boxes: Optional[int] = Field(0, description="Số thùng hỏng cần trừ khỏi tồn thực tế (nếu là DAMAGE_WRITE_OFF)")
    flag: Optional[str] = Field(None, description="Loại cờ gắn: SLOW_MOVING, NO_OUTBOUND, OTHER")
    note: Optional[str] = Field(None, description="Ghi chú hướng xử lý của Quản lý")

# --- Cờ & Biến động kho ---
class ItemFlagResponse(BaseModel):
    id: int
    item_id: int
    flag: str
    request_id: Optional[int]
    created_at: str

class StockMovementResponse(BaseModel):
    id: int
    item_id: int
    type: str
    boxes: int
    ref_type: Optional[str]
    ref_id: Optional[str]
    created_at: str

# --- Mẫu phản hồi lỗi chuẩn hệ thống ---
class StandardError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
