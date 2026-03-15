from fastapi import APIRouter, Depends
from app.inventory.dao import DAOTool, DAOStorage
from fastapi.exceptions import HTTPException
from app.schemas import Pagination
from typing import Annotated
from app.inventory.rb import InventorySearchFilter, CreateInventoryRB


router = APIRouter(prefix='/inventory', tags=['работа с инвентарем'])


@router.get('/', summary="Получить весь инвентарь")
async def get_all_inventory(pagination: Annotated[Pagination, Depends(Pagination)],
                      filter: Annotated[InventorySearchFilter, Depends(InventorySearchFilter)]):
    print(dict(filter))
    return await DAOTool.get_all_with_limit(pagination.limit, pagination.offset, **dict(filter))


@router.post('/create', summary="Добавить инвентарь")
async def create_inventory(inventory_info: CreateInventoryRB):
    print(dict(inventory_info))
    if await DAOStorage.check(name=inventory_info.storage_name):
        await DAOTool.create(**dict(inventory_info))
        return {'ok': True}
    return HTTPException(status_code=401, detail="Вы неправильно вписали значения в форму.")

