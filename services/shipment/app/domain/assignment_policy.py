"""Deadline rules by the role that created the assignment (Strategy pattern).

Each role allowed to assign is a subclass, so AssignmentService needs no if/else on roles.
"""
from abc import ABC, abstractmethod

from app.core.errors import Forbidden
from app.domain.enums import Decision, Role


class AssignmentPolicy(ABC):
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds

    @property
    @abstractmethod
    def timeout_decision(self) -> Decision:
        """Outcome when the deadline passes without a manager response."""


class ManagerPolicy(AssignmentPolicy):
    """Created by a manager: not confirmed within 30 seconds means rejected."""

    @property
    def timeout_decision(self) -> Decision:
        return Decision.REJECTED


class AuthorizedStaffPolicy(AssignmentPolicy):
    """Created by authorized staff: after 2 minutes it is auto-approved and that staff member is responsible."""

    @property
    def timeout_decision(self) -> Decision:
        return Decision.AUTO_APPROVED


class AssignmentPolicies:
    def __init__(self, confirm_ttl_sec: int, approval_ttl_sec: int):
        self._by_role: dict[Role, AssignmentPolicy] = {
            Role.MANAGER: ManagerPolicy(confirm_ttl_sec),
            Role.AUTHORIZED_STAFF: AuthorizedStaffPolicy(approval_ttl_sec),
        }

    def for_role(self, role: Role) -> AssignmentPolicy:
        policy = self._by_role.get(role)
        if policy is None:
            raise Forbidden("Vai trò không được phép gán hàng", details={"role": role})
        return policy
