from app.services.assignment_service import AssignmentService
from app.workers.periodic import PeriodicWorker


class AssignmentExpiryWorker(PeriodicWorker):
    """Scans PENDING assignments past expires_at (30 seconds or 2 minutes)."""
    name = "assignment-expiry"

    def __init__(self, assignments: AssignmentService):
        self._assignments = assignments

    def run_once(self) -> int:
        return self._assignments.expire_due()
