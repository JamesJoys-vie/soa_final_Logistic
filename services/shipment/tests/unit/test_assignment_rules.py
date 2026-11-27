"""Deadline rules by role and the responsibility trail."""
import pytest

from app.core.errors import Forbidden
from app.domain.assignment import Assignment
from app.domain.assignment_policy import AssignmentPolicies
from app.domain.enums import ApprovalType, AssignmentStatus, Decision, Role

policies = AssignmentPolicies(confirm_ttl_sec=30, approval_ttl_sec=120)


@pytest.mark.parametrize(("role", "ttl", "on_timeout"), [
    (Role.MANAGER, 30, Decision.REJECTED),
    (Role.AUTHORIZED_STAFF, 120, Decision.AUTO_APPROVED),
])
def test_policy_by_role(role, ttl, on_timeout):
    policy = policies.for_role(role)
    assert (policy.ttl_seconds, policy.timeout_decision) == (ttl, on_timeout)


def test_plain_staff_has_no_policy():
    with pytest.raises(Forbidden):
        policies.for_role(Role.STAFF)


@pytest.mark.parametrize(("decision", "decided_by", "responsible", "approval_type"), [
    (Decision.CONFIRMED, "manager", "manager", ApprovalType.MANUAL),
    (Decision.AUTO_APPROVED, None, "creator", ApprovalType.TIMEOUT),
    (Decision.REJECTED, "manager", None, None),
    (Decision.REJECTED, None, None, None),
    (Decision.WITHDRAWN, "creator", None, None),
])
def test_responsibility_trail(decision, decided_by, responsible, approval_type):
    assignment = Assignment(
        id=1, vehicle_id=1, plate="", destination="", created_by="creator", creator_role=Role.AUTHORIZED_STAFF,
        status=AssignmentStatus.PENDING, expires_at="x", decision=decision, decided_by=decided_by, decided_at="x",
        approval_type=None, responsible_user=None, created_at="x", lines=[])
    assert assignment.person_responsible == responsible
    assert decision.approval_type == approval_type


def test_every_visible_decision_is_a_final_status():
    visible = {d.value for d in Decision} - {Decision.CANCELLED}
    assert visible == {s.value for s in AssignmentStatus} - {AssignmentStatus.PENDING}
