from fastapi import APIRouter
from typing import List
from app.services.inventory_service import InventoryService
from app.schemas import StockDetailResponse, StockMovementResponse, ItemFlagResponse

router = APIRouter(prefix="/stock", tags=["Stock"])

@router.get("", response_model=List[StockDetailResponse], summary="Lấy danh sách tồn kho, tồn dự đoán và tồn khả dụng")
def get_all_stock():
    return InventoryService.get_all_stock()

@router.get("/movements", response_model=List[StockMovementResponse], summary="Lịch sử biến động nhập/xuất/điều chỉnh kho")
def get_movements(limit: int = 50):
    return InventoryService.get_movements(limit)

@router.get("/flags", response_model=List[ItemFlagResponse], summary="Danh sách hàng hóa bị cắm cờ do có vấn đề")
def get_flags():
    return InventoryService.get_flags()

@router.get("/{item_id}", response_model=StockDetailResponse, summary="Lấy chi tiết tồn kho của một mặt hàng")
def get_stock_by_item(item_id: int):
    return InventoryService.get_stock_by_item(item_id)
