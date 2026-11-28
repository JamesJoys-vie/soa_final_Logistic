"""Shared test helpers: sample users, tokens, a fake clock."""
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt

from app.core.clock import Clock
from app.core.config import Settings
from app.domain.enums import Role
from app.domain.user import CurrentUser

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_PATH = REPO_ROOT / "seed" / "seed.json"
JWT_SECRET = "test-secret-key-at-least-32-bytes-long"
INTERNAL_KEY = "test-internal-key"

MANAGER = CurrentUser("1", Role.MANAGER)
AUTHORIZED = CurrentUser("2", Role.AUTHORIZED_STAFF)
OTHER_AUTHORIZED = CurrentUser("3", Role.AUTHORIZED_STAFF)
STAFF = CurrentUser("4", Role.STAFF)


class FakeClock(Clock):
    """A frozen clock that only moves when a test calls advance()."""

    def __init__(self) -> None:
        self._now = datetime(2026, 11, 25, 8, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


def make_settings(tmp_path: Path, **overrides) -> Settings:
    return Settings(**{"jwt_secret": JWT_SECRET, "internal_api_key": INTERNAL_KEY,
                       "db_path": str(tmp_path / "shipment.db"), "seed_path": str(SEED_PATH), **overrides})


def make_token(user: CurrentUser, secret: str = JWT_SECRET, **overrides) -> str:
    claims = {"sub": user.id, "role": user.role.value, "exp": int(time.time()) + 3600, **overrides}
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, secret, algorithm="HS256")


def auth(user: CurrentUser) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user)}"}
