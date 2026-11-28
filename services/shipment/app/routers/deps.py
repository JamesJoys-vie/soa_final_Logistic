"""FastAPI dependencies: get services from the Container, verify the JWT, check the role."""
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from app.core.errors import Forbidden, Unauthorized
from app.domain.enums import Role
from app.domain.user import CurrentUser

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def current_user(container: ContainerDep,
                 credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> CurrentUser:
    if credentials is None:
        raise Unauthorized("Thiếu token Bearer")
    return container.token_verifier.verify(credentials.credentials)


class RequireRoles:
    def __init__(self, *roles: Role):
        self._roles = frozenset(roles)

    def __call__(self, user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
        if user.role not in self._roles:
            raise Forbidden("Vai trò không được phép thực hiện thao tác này",
                            details={"role": user.role, "allowed": sorted(self._roles)})
        return user


Manager = Annotated[CurrentUser, Depends(RequireRoles(Role.MANAGER))]
AuthorizedStaff = Annotated[CurrentUser, Depends(RequireRoles(Role.AUTHORIZED_STAFF))]
ManagerOrAuthorizedStaff = Annotated[CurrentUser, Depends(RequireRoles(Role.MANAGER, Role.AUTHORIZED_STAFF))]
