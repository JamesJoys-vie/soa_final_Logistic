"""Error responses documented in OpenAPI."""
from app.schemas.common import ErrorOut

_DESCRIPTIONS = {
    400: "Dữ liệu sai", 401: "Chưa đăng nhập", 403: "Sai vai trò", 404: "Không tìm thấy",
    409: "Xung đột trạng thái hoặc thiếu hàng", 502: "Inventory lỗi", 504: "Inventory quá hạn",
}


def errors(*statuses: int) -> dict:
    return {status: {"model": ErrorOut, "description": _DESCRIPTIONS[status]} for status in (400, 401, 403, *statuses)}
