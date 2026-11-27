import sqlite3

from app.domain.assignment import Assignment
from app.domain.enums import ApprovalType, AssignmentStatus, Decision, Role
from app.domain.line_item import LineItem
from app.domain.user import CurrentUser
from app.repositories.base import BaseRepository

_SELECT = "SELECT a.*, v.plate FROM assignments a JOIN vehicles v ON v.id = a.vehicle_id"


class AssignmentRepository(BaseRepository):
    """Tables assignments and assignment_lines."""

    # ---- create -----------------------------------------------------------------------
    def add(self, *, vehicle_id: int, destination: str, creator: CurrentUser, created_at: str,
            lines: list[LineItem]) -> int:
        """PENDING with no clock yet (expires_at NULL): locks the vehicle until Inventory reserves."""
        new_id = self._conn.execute(
            "INSERT INTO assignments (vehicle_id, destination, created_by, creator_role, status, created_at)"
            " VALUES (?, ?, ?, ?, 'PENDING', ?)",
            (vehicle_id, destination, creator.id, creator.role, created_at)).lastrowid
        self._insert_lines("assignment_lines", "assignment_id", new_id, lines)
        return new_id

    def start_clock(self, assignment_id: int, expires_at: str) -> bool:
        """Reservation done: start the deadline. False = the record was cancelled while waiting for Inventory."""
        return self._conn.execute(
            "UPDATE assignments SET expires_at = ?"
            " WHERE id = ? AND status = 'PENDING' AND decision IS NULL AND expires_at IS NULL",
            (expires_at, assignment_id)).rowcount == 1

    def remove(self, assignment_id: int) -> None:
        self._conn.execute("DELETE FROM assignments WHERE id = ? AND status = 'PENDING' AND expires_at IS NULL",
                           (assignment_id,))

    # ---- decision, step 1: claim --------------------------------------------
    def claim_by_user(self, assignment_id: int, decision: Decision, user_id: str, now: str) -> bool:
        return self._claim(assignment_id, decision, user_id, now, "expires_at > :now")

    def claim_on_timeout(self, assignment_id: int, decision: Decision, now: str) -> bool:
        return self._claim(assignment_id, decision, None, now, "expires_at <= :now")

    def claim_cancel(self, assignment_id: int, now: str) -> bool:
        return self._claim(assignment_id, Decision.CANCELLED, None, now, "expires_at IS NULL")

    def _claim(self, assignment_id: int, decision: Decision, decided_by: str | None, now: str, deadline: str) -> bool:
        """The HEART of race handling: confirm, reject, withdraw and expiry all go through this conditional UPDATE.

        1 row changed = won. 0 rows changed = someone else claimed it first, or the deadline is on the wrong side.
        """
        return self._conn.execute(
            "UPDATE assignments SET decision = :decision, decided_by = :decided_by, decided_at = :now"
            f" WHERE id = :id AND status = 'PENDING' AND decision IS NULL AND {deadline}",
            {"id": assignment_id, "decision": decision, "decided_by": decided_by, "now": now}).rowcount == 1

    # ---- decision, step 2: finish after Inventory has committed / released ---------------
    def finalize(self, assignment: Assignment) -> bool:
        """False = another call (request or worker) has already finished this decision."""
        return self._conn.execute(
            "UPDATE assignments SET status = decision, approval_type = ?, responsible_user = ?"
            " WHERE id = ? AND status = 'PENDING' AND decision = ?",
            (assignment.decision.approval_type, assignment.person_responsible, assignment.id,
             assignment.decision)).rowcount == 1

    # ---- read -----------------------------------------------------------------------
    def get(self, assignment_id: int) -> Assignment | None:
        found = self._all(f"{_SELECT} WHERE a.id = ?", (assignment_id,))
        return found[0] if found else None

    def find(self, status: AssignmentStatus | None, created_by: str | None, limit: int = 200) -> list[Assignment]:
        """Only assignments whose reservation is done, i.e. the ones users can actually see."""
        return self._all(
            f"{_SELECT} WHERE a.expires_at IS NOT NULL AND a.status = COALESCE(?, a.status)"
            " AND a.created_by = COALESCE(?, a.created_by) ORDER BY a.id DESC LIMIT ?", (status, created_by, limit))

    def pending_id_of(self, vehicle_id: int) -> int | None:
        return self.pending_ids_by_vehicle().get(vehicle_id)

    def pending_ids_by_vehicle(self) -> dict[int, int]:
        rows = self._conn.execute("SELECT vehicle_id, id FROM assignments WHERE status = 'PENDING'")
        return {row["vehicle_id"]: row["id"] for row in rows}

    def timed_out(self, now: str) -> list[Assignment]:
        return self._all(f"{_SELECT} WHERE a.status = 'PENDING' AND a.decision IS NULL AND a.expires_at <= ?"
                         " ORDER BY a.expires_at", (now,))

    def abandoned(self, created_before: str) -> list[Assignment]:
        """The process stopped between creation and a finished reservation."""
        return self._all(f"{_SELECT} WHERE a.status = 'PENDING' AND a.decision IS NULL AND a.expires_at IS NULL"
                         " AND a.created_at <= ?", (created_before,))

    def unfinished(self) -> list[Assignment]:
        return self._all(f"{_SELECT} WHERE a.status = 'PENDING' AND a.decision IS NOT NULL ORDER BY a.id", ())

    def _all(self, sql: str, params: tuple) -> list[Assignment]:
        rows = self._conn.execute(sql, params).fetchall()
        lines = self._lines("assignment_lines", "assignment_id", [row["id"] for row in rows])
        return [self._to_assignment(row, lines[row["id"]]) for row in rows]

    @staticmethod
    def _to_assignment(row: sqlite3.Row, lines: list[LineItem]) -> Assignment:
        return Assignment(
            id=row["id"], vehicle_id=row["vehicle_id"], plate=row["plate"], destination=row["destination"],
            created_by=row["created_by"], creator_role=Role(row["creator_role"]),
            status=AssignmentStatus(row["status"]), expires_at=row["expires_at"],
            decision=Decision(row["decision"]) if row["decision"] else None,
            decided_by=row["decided_by"], decided_at=row["decided_at"],
            approval_type=ApprovalType(row["approval_type"]) if row["approval_type"] else None,
            responsible_user=row["responsible_user"], created_at=row["created_at"], lines=lines)
