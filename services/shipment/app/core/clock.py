"""Shipment's clock. Tests replace it with the FakeClock subclass to move time forward."""
from datetime import UTC, datetime

# ISO 8601 UTC with a fixed length, so string comparison in SQL follows time order.
_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def now_iso(self) -> str:
        return self.to_iso(self.now())

    @staticmethod
    def to_iso(value: datetime) -> str:
        return value.astimezone(UTC).strftime(_FORMAT)
