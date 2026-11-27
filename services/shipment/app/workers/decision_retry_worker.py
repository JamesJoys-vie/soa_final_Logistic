from app.services.assignment_service import AssignmentService
from app.workers.periodic import PeriodicWorker


class DecisionRetryWorker(PeriodicWorker):
    """Retries Inventory for decisions whose reservation is not committed / released yet."""
    name = "decision-retry"

    def __init__(self, assignments: AssignmentService):
        self._assignments = assignments

    def run_once(self) -> int:
        return self._assignments.complete_unfinished()
