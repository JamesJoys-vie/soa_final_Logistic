-- Khởi tạo CSDL cho Inventory Service (Thành viên C: Nguyễn Đức Hiệu)
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

-- 1. Danh mục mặt hàng bảo hành (đồ điện tử, gia dụng, quần áo, văn phòng phẩm, nội thất)
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'thùng'
);

-- 2. Tồn kho cho từng mặt hàng (on_hand: tồn thực tế, incoming: xe chưa thả, allocated: xe chưa đi, reserved: đang giữ chỗ)
CREATE TABLE IF NOT EXISTS stock (
    item_id INTEGER PRIMARY KEY,
    on_hand INTEGER NOT NULL DEFAULT 0,
    incoming INTEGER NOT NULL DEFAULT 0,
    allocated INTEGER NOT NULL DEFAULT 0,
    reserved INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
);

-- 3. Quản lý các lượt giữ chỗ trọn gói cho lần gán hàng (Shipment)
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'COMMITTED', 'RELEASED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 4. Chi tiết từng dòng hàng của lượt giữ chỗ
CREATE TABLE IF NOT EXISTS reservation_lines (
    reservation_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    boxes INTEGER NOT NULL CHECK(boxes > 0),
    PRIMARY KEY (reservation_id, item_id),
    FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items (id)
);

-- 5. Lịch sử biến động kho (nhập, xuất, hủy do hỏng hóc, điều chỉnh)
CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('RECEIPT', 'DEPARTURE', 'DAMAGE_WRITE_OFF', 'ADJUSTMENT')),
    boxes INTEGER NOT NULL,
    ref_type TEXT, -- TRIP, ASSIGNMENT, REQUEST
    ref_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (item_id) REFERENCES items (id)
);

-- 6. Đánh dấu hàng hóa có vấn đề theo yêu cầu xử lý (Request Service)
CREATE TABLE IF NOT EXISTS item_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    flag TEXT NOT NULL, -- 'SLOW_MOVING', 'NO_OUTBOUND', 'DAMAGED', 'OTHER'
    request_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (item_id) REFERENCES items (id)
);

-- Chỉ mục hỗ trợ truy vấn nhanh
CREATE INDEX IF NOT EXISTS idx_stock_movements_item ON stock_movements(item_id);
CREATE INDEX IF NOT EXISTS idx_item_flags_item ON item_flags(item_id);
