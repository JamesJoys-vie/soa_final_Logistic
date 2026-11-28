"""Verify the JWT (HS256) issued by Auth. The gateway checks it; Shipment checks again with the same JWT_SECRET."""
import jwt

from app.core.errors import Unauthorized
from app.domain.enums import Role
from app.domain.user import CurrentUser


class TokenVerifier:
    def __init__(self, secret: str):
        self._secret = secret

    def verify(self, token: str) -> CurrentUser:
        try:
            claims = jwt.decode(token, self._secret, algorithms=["HS256"],
                                options={"require": ["exp", "sub", "role"]})
            return CurrentUser(id=claims["sub"], role=Role(claims["role"]))
        except jwt.ExpiredSignatureError as exc:
            raise Unauthorized("Phiên đăng nhập đã hết hạn", code="TOKEN_EXPIRED") from exc
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise Unauthorized("Token không hợp lệ", code="INVALID_TOKEN") from exc
