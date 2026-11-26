-- Khởi tạo CSDL cho Request Service (Thành viên C: Nguyễn Đức Hiệu)
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

-- 1. Bảng quản lý yêu cầu xử lý hàng hóa từ nhân viên
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('DAMAGED', 'SLOW_MOVING', 'NO_OUTBOUND', 'OTHER')),
    content TEXT NOT NULL,
    boxes INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'SUSPENDED', 'APPROVED', 'REJECTED')),
    created_by TEXT NOT NULL,
    response_note TEXT,
    decided_by TEXT,
    decided_at TEXT,
    suspend_deadline TEXT,
    auto_decided INTEGER NOT NULL DEFAULT 0,
    effect_status TEXT NOT NULL DEFAULT 'NONE' CHECK(effect_status IN ('NONE', 'APPLIED', 'FAILED', 'NOT_REQUIRED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2. Bảng lưu vết lịch sử chuyển đổi trạng thái (Audit trail)
CREATE TABLE IF NOT EXISTS request_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    note TEXT,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (request_id) REFERENCES requests (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created_by ON requests(created_by);
CREATE INDEX IF NOT EXISTS idx_request_history_req ON request_history(request_id);
