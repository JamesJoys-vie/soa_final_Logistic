from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

# Positive integer that fits SQLite's 64-bit INTEGER.
PositiveInt = Annotated[int, Field(gt=0, le=2**63 - 1)]


class LineSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: PositiveInt = Field(description="ID mặt hàng bên Inventory")
    boxes: PositiveInt = Field(description="Số thùng")


class ErrorOut(BaseModel):
    code: str
    message: str
    details: Any = None
