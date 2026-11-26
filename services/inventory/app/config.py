import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SERVICE_NAME: str = "inventory-service"
    PORT: int = 8002
    
    # Đường dẫn CSDL SQLite
    DB_PATH: str = os.getenv("DB_PATH", str(Path(__file__).resolve().parents[3] / "data" / "inventory" / "inventory.db"))
    
    # Khóa bí mật giao tiếp nội bộ giữa các microservices
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "warehouse_secret_internal_key_2026")
    
    # Đường dẫn file seed dữ liệu dùng chung
    SEED_PATH: str = os.getenv("SEED_PATH", str(Path(__file__).resolve().parents[3] / "seed" / "seed.json"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
