from pydantic import BaseModel, Field, field_validator

from app.domain.assignment import Assignment
from app.domain.enums import ApprovalType, AssignmentStatus, Decision, Role
from app.domain.line_item import LineItem
from app.schemas.common import LineSchema, PositiveInt


class AssignmentIn(BaseModel):
    vehicle_id: PositiveInt
    destination: str = Field(description="Vị trí đích")
    lines: list[LineSchema] = Field(min_length=1)

    @field_validator("destination")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Vị trí đích không được để trống")
        return value.strip()

    @field_validator("lines")
    @classmethod
    def _unique_items(cls, value: list[LineSchema]) -> list[LineSchema]:
        if len({line.item_id for line in value}) != len(value):
            raise ValueError("Mỗi mặt hàng chỉ xuất hiện một dòng")
        return value

    def to_lines(self) -> list[LineItem]:
        return [LineItem(line.item_id, line.boxes) for line in self.lines]


class AssignmentOut(BaseModel):
    id: int
    vehicle_id: int
    plate: str
    destination: str
    created_by: str
    creator_role: Role
    status: AssignmentStatus
    created_at: str
    expires_at: str
    server_time: str = Field(description="Giờ server, để frontend đếm ngược không phụ thuộc đồng hồ máy người dùng")
    decision: Decision | None = Field(description="Khác null khi status = PENDING: đã quyết định, đang chờ Inventory")
    decided_by: str | None
    decided_at: str | None
    approval_type: ApprovalType | None
    responsible_user: str | None
    lines: list[LineSchema]

    @classmethod
    def of(cls, assignment: Assignment, server_time: str) -> "AssignmentOut":
        fields = {name: getattr(assignment, name) for name in cls.model_fields if name not in ("server_time", "lines")}
        return cls(**fields, server_time=server_time,
                   lines=[LineSchema.model_validate(line) for line in assignment.lines])
