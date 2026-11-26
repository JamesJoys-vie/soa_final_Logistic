import pytest
import os
import sys
import tempfile
import time
from pathlib import Path
from fastapi import HTTPException
from pydantic import ValidationError

service_root = Path(__file__).resolve().parents[1]
for mod in list(sys.modules.keys()):
    if mod == "app" or mod.startswith("app."):
        del sys.modules[mod]

if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))
else:
    sys.path.remove(str(service_root))
    sys.path.insert(0, str(service_root))

temp_dir = tempfile.TemporaryDirectory()
temp_db_path = str(Path(temp_dir.name) / "test_request.db")
os.environ["DB_PATH"] = temp_db_path
os.environ["REQUEST_SUSPEND_TTL_SEC"] = "2" # Đặt 2 giây để test tự động từ chối
os.environ["INVENTORY_SERVICE_URL"] = "http://mock-inventory"

from app.database import init_db, get_connection
from app.services.request_service import RequestService
from app.schemas import (
    RequestCreate,
    RequestType,
    RequestApprove,
    RequestReject,
    RequestSuspend
)

init_db()

def test_create_request_default_pending():
    """Kiểm tra tạo yêu cầu mới: mặc định status PENDING và ghi lịch sử khởi tạo"""
    data = RequestCreate(
        item_id=1,
        type=RequestType.DAMAGED,
        content="Phát hiện 2 thùng tivi vỡ góc khi kiểm kê",
        boxes=2
    )
    req = RequestService.create_request(data, username="staff_nam")
    assert req["id"] is not None
    assert req["status"] == "PENDING"
    assert req["created_by"] == "staff_nam"
    assert req["boxes"] == 2
    assert len(req["history"]) == 1
    assert req["history"][0]["to_status"] == "PENDING"

def test_approve_missing_note_raises_validation_error():
    """Chấp thuận thiếu chỉ dẫn hoặc lý do: BẮT BUỘC trả lỗi 400 / ValidationError"""
    with pytest.raises(ValidationError):
        RequestApprove(response_note="")

    with pytest.raises(ValidationError):
        RequestApprove(response_note="   ")

def test_reject_missing_reason_raises_validation_error():
    """Từ chối thiếu lý do: BẮT BUỘC trả lỗi 400 / ValidationError"""
    with pytest.raises(ValidationError):
        RequestReject(response_note="")

    with pytest.raises(ValidationError):
        RequestReject(response_note="   ")

def test_suspend_request_and_deadline():
    """Kiểm tra quản lý chuyển sang trạng thái Treo: ghi nhận suspend_deadline"""
    data = RequestCreate(
        item_id=2,
        type=RequestType.SLOW_MOVING,
        content="Lô màn hình đã lưu kho quá 60 ngày",
        boxes=0
    )
    req = RequestService.create_request(data, username="staff_hoa")
    
    # Chuyển sang Treo
    suspended = RequestService.suspend_request(req["id"], username="manager_dung", data=RequestSuspend(note="Cần đợi ý kiến nhà cung ứng"))
    assert suspended["status"] == "SUSPENDED"
    assert suspended["suspend_deadline"] is not None
    assert len(suspended["history"]) == 2
    assert suspended["history"][1]["to_status"] == "SUSPENDED"

def test_auto_reject_expired_suspended_request():
    """
    Quy tắc nghiệp vụ cốt lõi:
    Yêu cầu ở trạng thái Treo quá thời hạn tự động chuyển sang Từ chối với lý do mặc định
    'Chưa có hướng xử lý từ phía quản lý', auto_decided = 1
    """
    data = RequestCreate(
        item_id=3,
        type=RequestType.OTHER,
        content="Yêu cầu kiểm định đột xuất lô bo mạch",
        boxes=0
    )
    req = RequestService.create_request(data, username="staff_hai")
    # Treo với TTL = 2s
    RequestService.suspend_request(req["id"], username="manager_dung")
    
    # Chờ 2.5 giây để hết hạn treo
    time.sleep(2.5)

    # Scheduler quét
    auto_count = RequestService.check_and_auto_reject_suspended()
    assert auto_count >= 1

    # Kiểm tra trạng thái yêu cầu sau khi quét
    updated = RequestService.get_request_by_id(req["id"])
    assert updated["status"] == "REJECTED"
    assert updated["auto_decided"] == 1
    assert updated["decided_by"] == "SYSTEM"
    assert "Chưa có hướng xử lý từ phía quản lý" in updated["response_note"]

def test_reject_request_success():
    """Kiểm tra quản lý chủ động từ chối yêu cầu kèm lý do"""
    data = RequestCreate(
        item_id=4,
        type=RequestType.NO_OUTBOUND,
        content="Lò vi sóng không có lịch xuất",
        boxes=0
    )
    req = RequestService.create_request(data, username="staff_hoa")
    
    rejected = RequestService.reject_request(
        req["id"],
        username="manager_dung",
        data=RequestReject(response_note="Kế hoạch xuất kho đã được dời sang tuần sau")
    )
    assert rejected["status"] == "REJECTED"
    assert rejected["response_note"] == "Kế hoạch xuất kho đã được dời sang tuần sau"
    assert rejected["decided_by"] == "manager_dung"

def test_conflict_on_finalized_request():
    """Không được phép chuyển trạng thái khi yêu cầu đã ở trạng thái cuối (APPROVED, REJECTED) -> 409 Conflict"""
    data = RequestCreate(
        item_id=5,
        type=RequestType.DAMAGED,
        content="Bao bì rách góc",
        boxes=1
    )
    req = RequestService.create_request(data, username="staff_nam")
    RequestService.reject_request(req["id"], username="manager_dung", data=RequestReject(response_note="Không đáng kể"))

    # Thử Treo một yêu cầu đã REJECTED
    with pytest.raises(HTTPException) as exc_info:
        RequestService.suspend_request(req["id"], username="manager_dung")
    assert exc_info.value.status_code == 409

    # Thử Từ chối lại
    with pytest.raises(HTTPException) as exc_info2:
        RequestService.reject_request(req["id"], username="manager_dung", data=RequestReject(response_note="Lại từ chối"))
    assert exc_info2.value.status_code == 409

def test_permission_filtering():
    """Kiểm tra phân quyền danh sách: Nhân viên chỉ thấy của mình, Quản lý thấy tất cả"""
    # staff_nam xem danh sách
    staff_view = RequestService.get_requests(username="staff_nam", role="STAFF")
    for r in staff_view:
        assert r["created_by"] == "staff_nam"

    # Quản lý xem toàn bộ
    manager_view = RequestService.get_requests(username="manager_dung", role="MANAGER")
    assert len(manager_view) >= len(staff_view)
