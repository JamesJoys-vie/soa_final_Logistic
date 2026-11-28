"""Outbound assignment: 5 states, deadline stored in expires_at."""
from dataclasses import dataclass

from app.core.errors import Conflict, Forbidden
from app.domain.enums import ApprovalType, AssignmentStatus, Decision, Role
from app.domain.line_item import LineItem
from app.domain.user import CurrentUser


@dataclass(frozen=True)
class Assignment:
    id: int
    vehicle_id: int
    plate: str
    destination: str
    created_by: str
    creator_role: Role
    status: AssignmentStatus
    expires_at: str | None
    decision: Decision | None
    decided_by: str | None
    decided_at: str | None
    approval_type: ApprovalType | None
    responsible_user: str | None
    created_at: str
    lines: list[LineItem]

    @property
    def is_pending(self) -> bool:
        return self.status == AssignmentStatus.PENDING

    @property
    def is_unfinished(self) -> bool:
        """Someone has claimed the decision but Inventory has not committed / released yet."""
        return self.is_pending and self.decision is not None

    @property
    def person_responsible(self) -> str | None:
        """Who is responsible for the shipment: the approving manager, or the creator when auto-approved."""
        if self.decision == Decision.CONFIRMED:
            return self.decided_by
        if self.decision == Decision.AUTO_APPROVED:
            return self.created_by
        return None

    def ensure_withdrawable_by(self, user: CurrentUser) -> None:
        if self.creator_role != Role.AUTHORIZED_STAFF or self.created_by != user.id:
            raise Forbidden("Chỉ nhân viên có thẩm quyền đã tạo lần gán mới được rút")

    def conflict(self) -> Conflict:
        """Why a late caller can no longer decide (409)."""
        if not self.is_pending or self.decision is not None:
            return Conflict("Lần gán đã được quyết định trước đó", code="ASSIGNMENT_ALREADY_DECIDED",
                            details={"assignment_id": self.id, "status": self.status, "decision": self.decision})
        return Conflict("Lần gán đã hết hạn", code="ASSIGNMENT_EXPIRED",
                        details={"assignment_id": self.id, "expires_at": self.expires_at})
