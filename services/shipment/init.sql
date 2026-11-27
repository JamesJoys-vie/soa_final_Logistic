-- Author: Phan Huy Bính (524H0081)
-- Shipment's own database (SQLite). Tables and columns follow section 4 of the programming plan.
-- item_id (Inventory) and user ids (Auth) are plain references, with NO cross-service foreign keys.
--
-- Columns added to the plan, each for a reason:
--   trips.assignment_id     which assignment created the outbound trip
--   assignments.decision    who claimed the decision while waiting for Inventory to commit / release
--   assignments.decided_at  when it was decided (responsibility trail, like the requests table)

CREATE TABLE IF NOT EXISTS vehicles (
    id           INTEGER PRIMARY KEY,
    plate        TEXT NOT NULL UNIQUE,
    driver_name  TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN (
                     'ARRIVING', 'WAITING_UNLOAD', 'UNLOADING',   -- inbound
                     'IDLE',                                      -- empty at the warehouse
                     'WAITING_LOAD', 'LOADING', 'DEPARTED'))      -- outbound
);

-- AUTOINCREMENT: assignment and trip ids are Inventory's idempotency keys and must never be reused.
CREATE TABLE IF NOT EXISTS assignments (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id        INTEGER NOT NULL REFERENCES vehicles(id),
    destination       TEXT NOT NULL,
    created_by        TEXT NOT NULL,
    creator_role      TEXT NOT NULL CHECK (creator_role IN ('MANAGER', 'AUTHORIZED_STAFF')),
    status            TEXT NOT NULL CHECK (status IN (
                          'PENDING', 'CONFIRMED', 'REJECTED', 'WITHDRAWN', 'AUTO_APPROVED')),
    expires_at        TEXT,   -- the single clock; NULL = reservation not finished, clock not started
    decision          TEXT CHECK (decision IN (
                          'CONFIRMED', 'REJECTED', 'WITHDRAWN', 'AUTO_APPROVED', 'CANCELLED')),
    decided_by        TEXT,   -- NULL = the system (timeout)
    decided_at        TEXT,
    approval_type     TEXT CHECK (approval_type IN ('MANUAL', 'TIMEOUT')),
    responsible_user  TEXT,
    created_at        TEXT NOT NULL
);
-- Vehicle lock: at most ONE PENDING assignment per vehicle.
CREATE UNIQUE INDEX IF NOT EXISTS ux_assignments_one_pending_per_vehicle
    ON assignments(vehicle_id) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS ix_assignments_pending_deadline
    ON assignments(expires_at) WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS assignment_lines (
    assignment_id  INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    item_id        INTEGER NOT NULL,
    boxes          INTEGER NOT NULL CHECK (boxes > 0),
    PRIMARY KEY (assignment_id, item_id)
);

CREATE TABLE IF NOT EXISTS trips (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id     INTEGER NOT NULL REFERENCES vehicles(id),
    direction      TEXT NOT NULL CHECK (direction IN ('IN', 'OUT')),
    destination    TEXT,
    assignment_id  INTEGER UNIQUE REFERENCES assignments(id),
    created_at     TEXT NOT NULL,
    closed_at      TEXT,      -- NULL = not unloaded yet (IN) or not departed yet (OUT)
    CHECK (direction = 'OUT' OR (assignment_id IS NULL AND destination IS NULL))
);

CREATE TABLE IF NOT EXISTS trip_lines (
    trip_id  INTEGER NOT NULL REFERENCES trips(id),
    item_id  INTEGER NOT NULL,
    boxes    INTEGER NOT NULL CHECK (boxes > 0),
    PRIMARY KEY (trip_id, item_id)
);

CREATE TABLE IF NOT EXISTS vehicle_status_history (
    id           INTEGER PRIMARY KEY,
    vehicle_id   INTEGER NOT NULL REFERENCES vehicles(id),
    from_status  TEXT NOT NULL,
    to_status    TEXT NOT NULL,
    changed_by   TEXT,        -- NULL = the system
    changed_at   TEXT NOT NULL
);
