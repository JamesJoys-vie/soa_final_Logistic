import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SERVICE_NAME: str = "request-service"
    PORT: int = 8004
    
    # Đường dẫn CSDL SQLite riêng của Request Service
    DB_PATH: str = os.getenv("DB_PATH", str(Path(__file__).resolve().parents[3] / "data" / "request" / "request.db"))
    
    # Hạn trạng thái Treo: mặc định 4 giờ (14400 giây), cấu hình rút ngắn được khi demo
    REQUEST_SUSPEND_TTL_SEC: int = int(os.getenv("REQUEST_SUSPEND_TTL_SEC", "14400"))
    
    # Chu kỳ quét của scheduler (giây)
    SCHEDULER_INTERVAL_SEC: int = int(os.getenv("SCHEDULER_INTERVAL_SEC", "5"))
    
    # URL gọi nội bộ sang Inventory Service
    INVENTORY_SERVICE_URL: str = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8002")
    
    # Khóa dịch vụ nội bộ
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "warehouse_secret_internal_key_2026")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
