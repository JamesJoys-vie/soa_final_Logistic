"""Service settings, read once from environment variables at startup."""
import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """A required variable is missing: stop now instead of running with an unsafe default key."""


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    internal_api_key: str
    db_path: str = "/data/shipment.db"
    seed_path: str = "/seed/seed.json"
    inventory_url: str = "http://inventory:8002"
    http_timeout_sec: float = 3.0
    assign_confirm_ttl_sec: int = 30    # confirmation deadline for assignments created by a manager
    assign_approval_ttl_sec: int = 120  # approval deadline for assignments created by authorized staff
    scheduler_interval_sec: float = 2.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        missing = [name for name in ("JWT_SECRET", "INTERNAL_API_KEY") if not env.get(name)]
        if missing:
            raise ConfigError(f"Thiếu biến môi trường bắt buộc: {', '.join(missing)}")
        return cls(
            jwt_secret=env["JWT_SECRET"],
            internal_api_key=env["INTERNAL_API_KEY"],
            db_path=env.get("DB_PATH", cls.db_path),
            seed_path=env.get("SEED_PATH", cls.seed_path),
            inventory_url=env.get("INVENTORY_URL", cls.inventory_url),
            http_timeout_sec=float(env.get("HTTP_TIMEOUT_SEC", cls.http_timeout_sec)),
            assign_confirm_ttl_sec=int(env.get("ASSIGN_CONFIRM_TTL_SEC", cls.assign_confirm_ttl_sec)),
            assign_approval_ttl_sec=int(env.get("ASSIGN_APPROVAL_TTL_SEC", cls.assign_approval_ttl_sec)),
            scheduler_interval_sec=float(env.get("SCHEDULER_INTERVAL_SEC", cls.scheduler_interval_sec)),
        )
