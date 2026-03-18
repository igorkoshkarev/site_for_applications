from app.inventory.models import Tool, Cabinet
from app.dao import BaseDAO


class DAOTool(BaseDAO):
    model = Tool
    ID = model.inventory_number


class DAOCabinet(BaseDAO):
    model = Cabinet
