from app.inventory.models import Tool, Storage
from app.dao import BaseDAO


class DAOTool(BaseDAO):
    model = Tool

class DAOStorage(BaseDAO):
    model = Storage
