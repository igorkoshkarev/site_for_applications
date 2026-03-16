from pydantic import BaseModel, Field
from app.inventory.models import Status


class InventorySearchFilter(BaseModel):
    name: str|None = Field(None)
    status: Status|None = Field(None)
    cabinet_name: str|None = Field(None)


class CreateInventoryRB(BaseModel):
    inventory_number: str
    name: str
    status: Status
    cabinet_name: str
