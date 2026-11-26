from fastapi import APIRouter
from typing import List
from app.services.inventory_service import InventoryService
from app.schemas import ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])

@router.get("", response_model=List[ItemResponse], summary="Lấy danh mục hàng hóa trong kho")
def get_items():
    return InventoryService.get_all_items()
