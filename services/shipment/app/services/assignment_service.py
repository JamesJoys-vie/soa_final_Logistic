"""Assign outbound goods to an empty vehicle and handle races while waiting for confirmation (section 5).

Every decision (confirm, reject, withdraw, expiry) takes two steps:
  1. Claim it in shipment.db with a conditional UPDATE: one caller wins, a late caller gets 409.
  2. Ask Inventory to commit or release the reservation, and change the state only AFTER it succeeds.
If Inventory fails in step 2: the assignment stays PENDING, the vehicle stays locked, the stock stays reserved,
and a worker retries until it is done.
"""
import logging
from datetime import timedelta

from app.clients.inventory_gateway import InventoryGateway
from app.core.clock import Clock
from app.core.errors import AppError, Conflict, NotFound, UpstreamTimeout
from app.core.metrics import Metrics
from app.domain.assignment import Assignment
from app.domain.assignment_policy import AssignmentPolicies
from app.domain.enums import AssignmentStatus, Decision, TripDirection, VehicleStatus
from app.domain.line_item import LineItem
from app.domain.user import CurrentUser
from app.repositories.unit_of_work import UnitOfWork, UnitOfWorkFactory

log = logging.getLogger("shipment.assignments")

# An assignment still unreserved after this long means the process stopped half way.
RESERVATION_GRACE = timedelta(seconds=60)


class AssignmentService:
    def __init__(self, uow: UnitOfWorkFactory, inventory: InventoryGateway, policies: AssignmentPolicies,
                 clock: Clock, metrics: Metrics):
        self._uow = uow
        self._inventory = inventory
        self._policies = policies
        self._clock = clock
        self._metrics = metrics

    # ---- Xem -----------------------------------------------------------------------
    def find(self, user: CurrentUser, status: AssignmentStatus | None) -> list[Assignment]:
        """Managers see all (approval inbox). Authorized staff only see their own assignments."""
        with self._uow.read() as uow:
            return uow.assignments.find(status, None if user.is_manager else user.id)

    # ---- Create -----------------------------------------------------------------------
    def create(self, user: CurrentUser, vehicle_id: int, destination: str, lines: list[LineItem]) -> Assignment:
        policy = self._policies.for_role(user.role)
        assignment_id = self._lock_vehicle(user, vehicle_id, destination, lines)
        self._reserve(assignment_id, lines)
        self._start_clock(assignment_id, policy.ttl_seconds)
        self._metrics.assignment_entered(AssignmentStatus.PENDING)
        log.info("assignment %s created by user %s (%s)", assignment_id, user.id, user.role)
        return self._load(assignment_id)

    def _lock_vehicle(self, user: CurrentUser, vehicle_id: int, destination: str, lines: list[LineItem]) -> int:
        with self._uow.transaction() as uow:
            vehicle = uow.vehicles.get(vehicle_id)
            if vehicle is None:
                raise NotFound("Không tìm thấy xe", details={"vehicle_id": vehicle_id})
            vehicle.ensure_assignable()
            pending_id = uow.assignments.pending_id_of(vehicle_id)
            if pending_id is not None:
                raise Conflict("Xe đang có một lần gán chờ xác nhận", code="VEHICLE_LOCKED",
                               details={"vehicle_id": vehicle_id, "assignment_id": pending_id})
            return uow.assignments.add(vehicle_id=vehicle_id, destination=destination, creator=user,
                                       created_at=self._clock.now_iso(), lines=lines)

    def _reserve(self, assignment_id: int, lines: list[LineItem]) -> None:
        try:
            self._inventory.reserve(assignment_id, lines)
        except Conflict:   # Inventory clearly reserved nothing: treat the assignment as never created
            with self._uow.transaction() as uow:
                uow.assignments.remove(assignment_id)
            raise
        except AppError:   # unknown whether Inventory reserved: release to be safe, then delete
            self._cancel(assignment_id)
            raise

    def _start_clock(self, assignment_id: int, ttl_seconds: int) -> None:
        expires_at = self._clock.to_iso(self._clock.now() + timedelta(seconds=ttl_seconds))
        with self._uow.transaction() as uow:
            started = uow.assignments.start_clock(assignment_id, expires_at)
        if not started:    # reservation took too long and a worker cancelled it: release what was just reserved
            self._inventory.release(assignment_id)
            raise UpstreamTimeout("Inventory giữ chỗ quá lâu", code="INVENTORY_TIMEOUT")

    def _cancel(self, assignment_id: int) -> bool:
        """Only claims the cancellation; a worker releases the reservation and deletes the record on its next run."""
        with self._uow.transaction() as uow:
            return uow.assignments.claim_cancel(assignment_id, self._clock.now_iso())

    # ---- User decisions ---------------------------------------------------
    def confirm(self, user: CurrentUser, assignment_id: int) -> Assignment:
        return self._decide(user, assignment_id, Decision.CONFIRMED)

    def reject(self, user: CurrentUser, assignment_id: int) -> Assignment:
        return self._decide(user, assignment_id, Decision.REJECTED)

    def withdraw(self, user: CurrentUser, assignment_id: int) -> Assignment:
        self._load(assignment_id).ensure_withdrawable_by(user)
        return self._decide(user, assignment_id, Decision.WITHDRAWN)

    def _decide(self, user: CurrentUser, assignment_id: int, decision: Decision) -> Assignment:
        with self._uow.transaction() as uow:
            won = uow.assignments.claim_by_user(assignment_id, decision, user.id, self._clock.now_iso())
        if not won:
            raise self._load(assignment_id).conflict()
        self._complete(assignment_id)
        return self._load(assignment_id)

    # ---- System decisions (called by workers) -----------------------------------------
    def expire_due(self) -> int:
        """Expired: apply the rule of the creator's role. Abandoned during reservation: cancel."""
        now = self._clock.now()
        with self._uow.read() as uow:
            timed_out = uow.assignments.timed_out(self._clock.to_iso(now))
            abandoned = uow.assignments.abandoned(self._clock.to_iso(now - RESERVATION_GRACE))
        expired = 0
        for assignment in timed_out:
            decision = self._policies.for_role(assignment.creator_role).timeout_decision
            with self._uow.transaction() as uow:
                won = uow.assignments.claim_on_timeout(assignment.id, decision, self._clock.to_iso(now))
            if won:        # losing means a user decided just before
                expired += 1
                self._try_complete(assignment.id)
        return expired + sum(self._cancel(assignment.id) for assignment in abandoned)

    def complete_unfinished(self) -> int:
        """Retry Inventory for decisions that were claimed but not finished."""
        with self._uow.read() as uow:
            unfinished = uow.assignments.unfinished()
        return sum(self._try_complete(assignment.id) for assignment in unfinished)

    # ---- Finish a decision ----------------------------------------------------------
    def _try_complete(self, assignment_id: int) -> bool:
        try:
            self._complete(assignment_id)
            return True
        except AppError as exc:
            log.warning("assignment %s not completed yet, will retry: %s", assignment_id, exc.code)
            return False

    def _complete(self, assignment_id: int) -> None:
        """Safe to call repeatedly: Inventory is idempotent and finalize is conditional."""
        with self._uow.read() as uow:
            assignment = uow.assignments.get(assignment_id)
        if assignment is None or not assignment.is_unfinished:
            return
        if assignment.decision.approves:
            self._inventory.commit(assignment_id)
        else:
            self._inventory.release(assignment_id)

        with self._uow.transaction() as uow:
            if assignment.decision == Decision.CANCELLED:
                uow.assignments.remove(assignment_id)
                return
            if not uow.assignments.finalize(assignment):
                return
            if assignment.decision.approves:
                self._dispatch(uow, assignment)
        self._metrics.assignment_entered(assignment.decision)
        log.info("assignment %s -> %s", assignment_id, assignment.decision)

    def _dispatch(self, uow: UnitOfWork, assignment: Assignment) -> None:
        """Assignment takes effect: create the outbound trip and set the vehicle to WAITING_LOAD, one transaction."""
        now = self._clock.now_iso()
        uow.trips.add(vehicle_id=assignment.vehicle_id, direction=TripDirection.OUT, lines=assignment.lines,
                      destination=assignment.destination, assignment_id=assignment.id, created_at=now)
        moved = uow.vehicles.move(assignment.vehicle_id, VehicleStatus.IDLE, VehicleStatus.WAITING_LOAD,
                                  changed_by=assignment.decided_by, now=now)
        if not moved:  # the vehicle lock prevents this; if it happens, roll back both the state and the trip
            raise Conflict("Xe không còn ở trạng thái Đang trống", code="VEHICLE_NOT_IDLE",
                           details={"vehicle_id": assignment.vehicle_id})

    def _load(self, assignment_id: int) -> Assignment:
        with self._uow.read() as uow:
            assignment = uow.assignments.get(assignment_id)
        if assignment is None or assignment.expires_at is None:
            raise NotFound("Không tìm thấy lần gán", details={"assignment_id": assignment_id})
        return assignment
