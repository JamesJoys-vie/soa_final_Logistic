from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum

class RequestType(str, Enum):
    DAMAGED = "DAMAGED"             # Hỏng hóc
    SLOW_MOVING = "SLOW_MOVING"     # Hàng tồn quá lâu
    NO_OUTBOUND = "NO_OUTBOUND"     # Không có lượt xuất kho
    OTHER = "OTHER"                 # Khác

class RequestStatus(str, Enum):
    PENDING = "PENDING"             # Chờ xử lý (khởi tạo mặc định)
    SUSPENDED = "SUSPENDED"         # Treo (hạn 4 giờ)
    APPROVED = "APPROVED"           # Chấp thuận
    REJECTED = "REJECTED"           # Từ chối

class RequestCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="Mã mặt hàng cần xử lý")
    type: RequestType = Field(..., description="Loại yêu cầu: DAMAGED, SLOW_MOVING, NO_OUTBOUND, OTHER")
    content: str = Field(..., min_length=3, description="Nội dung mô tả ngắn gọn vấn đề")
    boxes: Optional[int] = Field(0, ge=0, description="Số thùng liên quan (ví dụ số thùng hỏng)")

class RequestSuspend(BaseModel):
    note: Optional[str] = Field(None, description="Ghi chú khi chuyển sang trạng thái Treo")

class RequestApprove(BaseModel):
    response_note: str = Field(..., min_length=1, description="Chỉ dẫn hoặc lý do phê duyệt (bắt buộc)")
    
    @field_validator("response_note")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chấp thuận bắt buộc phải có chỉ dẫn hoặc lý do cụ thể")
        return v.strip()

class RequestReject(BaseModel):
    response_note: str = Field(..., min_length=1, description="Lý do từ chối yêu cầu (bắt buộc)")

    @field_validator("response_note")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Từ chối bắt buộc phải có lý do cụ thể")
        return v.strip()

class RequestHistoryResponse(BaseModel):
    id: int
    from_status: Optional[str]
    to_status: str
    changed_by: str
    note: Optional[str]
    changed_at: str

class RequestResponse(BaseModel):
    id: int
    item_id: int
    type: str
    content: str
    boxes: int
    status: str
    created_by: str
    response_note: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    suspend_deadline: Optional[str] = None
    auto_decided: int = 0
    effect_status: str
    created_at: str
    history: Optional[List[RequestHistoryResponse]] = []
