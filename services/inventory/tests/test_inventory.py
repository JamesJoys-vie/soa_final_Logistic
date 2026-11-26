import pytest
import os
import sys
import tempfile
from pathlib import Path
from fastapi import HTTPException

# Thêm đường dẫn service vào sys.path
service_root = Path(__file__).resolve().parents[1]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

# Thiết lập file CSDL tạm cho test
temp_dir = tempfile.TemporaryDirectory()
temp_db_path = str(Path(temp_dir.name) / "test_inventory.db")
os.environ["DB_PATH"] = temp_db_path
os.environ["INTERNAL_API_KEY"] = "test_internal_key_123"

from app.database import init_db
from app.services.inventory_service import InventoryService
from app.schemas import (
    ReservationCreateRequest,
    ReservationLineCreate,
    TripReceiptRequest,
    TripLineItem,
    TripDepartureRequest,
    AdjustmentRequest
)
from app.routers.internal import verify_internal_key

# Khởi tạo DB tạm và seed dữ liệu trước khi chạy test
init_db()

def test_items_and_stock_formula():
    """Kiểm tra danh mục hàng và công thức:
       - Tồn dự đoán = on_hand + incoming - allocated
       - Tồn khả dụng = on_hand - allocated - reserved
    """
    items = InventoryService.get_all_items()
    assert len(items) >= 10

    stocks = InventoryService.get_all_stock()
    assert len(stocks) >= 10

    first = stocks[0]
    expected_projected = first["on_hand"] + first["incoming"] - first["allocated"]
    expected_available = first["on_hand"] - first["allocated"] - first["reserved"]
    assert first["projected_stock"] == expected_projected
    assert first["available_stock"] == expected_available

def test_reservation_flow_success():
    """Kiểm tra luồng giữ chỗ trọn gói thành công và chốt giữ chỗ (commit)"""
    item1 = InventoryService.get_stock_by_item(1)
    init_reserved = item1["reserved"]
    init_allocated = item1["allocated"]

    assign_id = "ASSIGN-TEST-001"
    req = ReservationCreateRequest(
        assignment_id=assign_id,
        lines=[ReservationLineCreate(item_id=1, boxes=5)]
    )
    res = InventoryService.create_reservation(req)
    assert res["status"] == "ACTIVE"

    # Kiểm tra reserved đã tăng thêm 5
    after = InventoryService.get_stock_by_item(1)
    assert after["reserved"] == init_reserved + 5

    # Idempotent: Gửi lại cùng assignment_id trả về đúng bản ghi không bị cộng dồn
    retry = InventoryService.create_reservation(req)
    assert retry["status"] == "ACTIVE"
    assert InventoryService.get_stock_by_item(1)["reserved"] == init_reserved + 5

    # Commit giữ chỗ: reserved giảm 5, allocated tăng 5
    commit_res = InventoryService.commit_reservation(assign_id)
    assert commit_res["status"] == "COMMITTED"

    committed = InventoryService.get_stock_by_item(1)
    assert committed["reserved"] == init_reserved
    assert committed["allocated"] == init_allocated + 5

def test_reservation_insufficient_stock_fails():
    """Kiểm tra thiếu hàng: bắn HTTPException 409 kèm chi tiết dòng thiếu"""
    item2 = InventoryService.get_stock_by_item(2)
    excess_boxes = item2["available_stock"] + 9999

    req = ReservationCreateRequest(
        assignment_id="ASSIGN-FAIL-001",
        lines=[ReservationLineCreate(item_id=2, boxes=excess_boxes)]
    )
    with pytest.raises(HTTPException) as exc_info:
        InventoryService.create_reservation(req)

    assert exc_info.value.status_code == 409
    err = exc_info.value.detail
    assert err["code"] == "STOCK_INSUFFICIENT"
    assert len(err["details"]) > 0
    assert err["details"][0]["item_id"] == 2

def test_release_reservation():
    """Kiểm tra nhả giữ chỗ khi lần gán bị từ chối hoặc rút: hoàn lại reserved"""
    assign_id = "ASSIGN-RELEASE-001"
    item3 = InventoryService.get_stock_by_item(3)
    init_reserved = item3["reserved"]

    req = ReservationCreateRequest(
        assignment_id=assign_id,
        lines=[ReservationLineCreate(item_id=3, boxes=10)]
    )
    InventoryService.create_reservation(req)
    assert InventoryService.get_stock_by_item(3)["reserved"] == init_reserved + 10

    # Nhả giữ chỗ
    rel = InventoryService.release_reservation(assign_id)
    assert rel["status"] == "RELEASED"
    assert InventoryService.get_stock_by_item(3)["reserved"] == init_reserved

def test_receipt_and_departure():
    """Kiểm tra xe đến thả hàng (incoming -> on_hand) và xe đi rời kho (trừ on_hand và allocated)"""
    item4 = InventoryService.get_stock_by_item(4)
    init_on_hand = item4["on_hand"]
    init_incoming = item4["incoming"]

    # Xe đến hoàn thành thả hàng 10 thùng
    InventoryService.process_receipt(TripReceiptRequest(
        trip_id="TRIP-IN-001",
        lines=[TripLineItem(item_id=4, boxes=10)]
    ))
    after_rec = InventoryService.get_stock_by_item(4)
    assert after_rec["on_hand"] == init_on_hand + 10
    assert after_rec["incoming"] == max(0, init_incoming - 10)

    # Xe xuất kho rời khỏi kho 5 thùng
    init_allocated = after_rec["allocated"]
    InventoryService.process_departure(TripDepartureRequest(
        trip_id="TRIP-OUT-001",
        lines=[TripLineItem(item_id=4, boxes=5)]
    ))
    after_dep = InventoryService.get_stock_by_item(4)
    assert after_dep["on_hand"] == after_rec["on_hand"] - 5
    assert after_dep["allocated"] == max(0, init_allocated - 5)

def test_damage_write_off_adjustment():
    """Kiểm tra điều chỉnh trừ tồn thực tế khi yêu cầu Hỏng hóc được Chấp thuận"""
    item5 = InventoryService.get_stock_by_item(5)
    init_on_hand = item5["on_hand"]

    adj_res = InventoryService.process_adjustment(AdjustmentRequest(
        request_id=202,
        item_id=5,
        action="DAMAGE_WRITE_OFF",
        boxes=4,
        note="Tiêu hủy hàng lỗi theo chỉ dẫn quản lý"
    ))
    assert adj_res["action"] == "DAMAGE_WRITE_OFF"
    assert InventoryService.get_stock_by_item(5)["on_hand"] == init_on_hand - 4

def test_internal_key_security():
    """Kiểm tra bảo mật API nội bộ qua header X-Internal-Key"""
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_key(x_internal_key="wrong_key")
    assert exc_info.value.status_code == 403
