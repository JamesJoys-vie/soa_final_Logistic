import pytest

from app.core.config import ConfigError, Settings

REQUIRED = {"JWT_SECRET": "a", "INTERNAL_API_KEY": "b"}


def test_defaults_match_the_assignment():
    settings = Settings.from_env(REQUIRED)
    assert (settings.assign_confirm_ttl_sec, settings.assign_approval_ttl_sec) == (30, 120)


def test_deadlines_come_from_environment():
    settings = Settings.from_env({**REQUIRED, "ASSIGN_CONFIRM_TTL_SEC": "5", "ASSIGN_APPROVAL_TTL_SEC": "8"})
    assert (settings.assign_confirm_ttl_sec, settings.assign_approval_ttl_sec) == (5, 8)


@pytest.mark.parametrize("missing", REQUIRED)
def test_refuses_to_start_without_secrets(missing):
    with pytest.raises(ConfigError, match=missing):
        Settings.from_env({k: v for k, v in REQUIRED.items() if k != missing})
