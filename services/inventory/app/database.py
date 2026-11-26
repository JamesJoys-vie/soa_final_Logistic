import sqlite3
import json
import os
from pathlib import Path
from app.config import settings

def get_connection() -> sqlite3.Connection:
    """Tạo kết nối SQLite riêng cho Inventory Service, cấu hình WAL và timeout"""
    db_file = Path(settings.DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # isolation_level=None để kiểm soát thủ công các transaction BEGIN IMMEDIATE
    conn = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Khởi tạo cấu trúc bảng từ init.sql và seed dữ liệu nếu bảng trống"""
    init_sql_path = Path(__file__).resolve().parents[1] / "init.sql"
    if not init_sql_path.exists():
        raise FileNotFoundError(f"Không tìm thấy init.sql tại {init_sql_path}")
        
    with open(init_sql_path, "r", encoding="utf-8") as f:
        sql_script = f.read()
        
    conn = get_connection()
    try:
        conn.executescript(sql_script)
        
        # Kiểm tra xem đã có dữ liệu items chưa, nếu chưa thì nạp từ seed.json
        cursor = conn.execute("SELECT COUNT(*) as count FROM items")
        row = cursor.fetchone()
        if row and row["count"] == 0:
            seed_path = Path(settings.SEED_PATH)
            if seed_path.exists():
                with open(seed_path, "r", encoding="utf-8") as sf:
                    seed_data = json.load(sf)
                    items = seed_data.get("items", [])
                    
                    conn.execute("BEGIN IMMEDIATE")
                    for it in items:
                        conn.execute(
                            "INSERT INTO items (id, sku, name, category, unit) VALUES (?, ?, ?, ?, ?)",
                            (it["id"], it["sku"], it["name"], it["category"], it["unit"])
                        )
                        st = it.get("initial_stock", {})
                        conn.execute(
                            "INSERT INTO stock (item_id, on_hand, incoming, allocated, reserved) VALUES (?, ?, ?, ?, ?)",
                            (
                                it["id"],
                                st.get("on_hand", 0),
                                st.get("incoming", 0),
                                st.get("allocated", 0),
                                st.get("reserved", 0)
                            )
                        )
                    conn.execute("COMMIT")
                    print(f"[Inventory] Đã khởi tạo {len(items)} mặt hàng mẫu từ seed.json")
    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"[Inventory] Lỗi khi khởi tạo CSDL: {e}")
        raise e
    finally:
        conn.close()
