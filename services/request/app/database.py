import sqlite3
from pathlib import Path
from app.config import settings

def get_connection() -> sqlite3.Connection:
    """Tạo kết nối SQLite riêng cho Request Service"""
    db_file = Path(settings.DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Khởi tạo cấu trúc bảng từ init.sql"""
    init_sql_path = Path(__file__).resolve().parents[1] / "init.sql"
    if not init_sql_path.exists():
        raise FileNotFoundError(f"Không tìm thấy init.sql tại {init_sql_path}")
        
    with open(init_sql_path, "r", encoding="utf-8") as f:
        sql_script = f.read()
        
    conn = get_connection()
    try:
        conn.executescript(sql_script)
        print("[Request] CSDL Request Service đã sẵn sàng")
    finally:
        conn.close()
