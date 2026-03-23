from pydantic import BaseModel, Field
from app.inventory.models import ToolStatus


class InventorySearchFilter(BaseModel):
    name: str|None = Field(None)
    status: ToolStatus|None = Field(None)
    cabinet_name: str|None = Field(None)


class CreateInventoryRB(BaseModel):
    inventory_number: str
    name: str
    status: ToolStatus = Field(ToolStatus.in_storage)
    cabinet_name: str
