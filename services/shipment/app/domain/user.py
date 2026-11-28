from dataclasses import dataclass

from app.domain.enums import Role


@dataclass(frozen=True)
class CurrentUser:
    """The current user, taken from the JWT. Shipment does not store users, it only refers to their ID."""
    id: str
    role: Role

    @property
    def is_manager(self) -> bool:
        return self.role == Role.MANAGER
