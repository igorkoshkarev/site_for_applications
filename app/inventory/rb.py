from pydantic import BaseModel, Field
from app.inventory.models import ToolStatus


class InventorySearchFilter(BaseModel):
    name: str|None = Field(None)
    status: ToolStatus|None = Field(None)
    cabinet_name: str|None = Field(None)


class CreateInventoryRB(BaseModel):
    inventory_number: str = Field(..., min_length=1, max_length=30, description='Инвентарный номер инструмента')
    name: str = Field(..., min_length=1, max_length=30, description='Название инструмента')
    status: ToolStatus = Field(ToolStatus.in_storage, description='Статус использования инструмента')
    cabinet_name: str = Field(..., description='Кабинет где лежит инструмент')
