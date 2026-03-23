from fastapi import APIRouter, Depends, Form
from app.inventory.dao import DAOTool, DAOCabinet
from fastapi.exceptions import HTTPException
from app.schemas import PaginationModel
from typing import Annotated
from app.inventory.rb import InventorySearchFilter, CreateInventoryRB
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from app.inventory.models import ToolStatus


router = APIRouter(prefix='/inventory', tags=['работа с инвентарем'])
templates = Jinja2Templates(directory='app/templates')

@router.get('/item/{inventory_number}/equip', summary="Взять инвентарную вещь")
async def equip_inventory_item(inventory_number: str):
    await DAOTool.update_one(inventory_number, **{'status': ToolStatus.used})
    response = RedirectResponse('/inventory', status_code=302)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get('/item/{inventory_number}/put', summary="Положить инвентарную вещь на склад")
async def put_inventory_item(inventory_number: str):
    await DAOTool.update_one(inventory_number, **{'status': ToolStatus.in_storage})
    response = RedirectResponse('/inventory', status_code=302)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get('/', summary="Получить весь инвентарь")
async def get_all_inventory(request: Request,
                    pagination: Annotated[PaginationModel, Depends()],
                    filter: Annotated[InventorySearchFilter, Depends()]):
    inventory = await DAOTool.get_all_with_limit(pagination.limit, pagination.get_offset(), **dict(filter))
    return templates.TemplateResponse('inventory.html', {
        'user': request.state.user,
        'request': request,
        'inventory': inventory,
        'status': ToolStatus
    })

@router.get('/create', summary="Страница добавления инвентаря")
async def create_inventory_page(request: Request):
    cabinets = await DAOCabinet.get_all(columns=['name'])
    return templates.TemplateResponse('create_inventory_item.html', {
        'user': request.state.user,
        'request': request,
        'cabinets': cabinets,
        'status': ToolStatus

    })
    if await DAOCabinet.check(name=inventory_info.cabinet_name):
        await DAOTool.create(**dict(inventory_info))
        return RedirectResponse('/inventory', status_code=301)
    return HTTPException(status_code=401, detail="Вы неправильно вписали значения в форму.")


@router.post('/create', summary="Добавить инвентарь")
async def create_inventory(request: Request, inventory_info: Annotated[CreateInventoryRB, Form()]):
    if await DAOCabinet.check(name=inventory_info.cabinet_name):
        await DAOTool.create(**dict(inventory_info))
        return RedirectResponse('/inventory', status_code=301)
    return HTTPException(status_code=401, detail="Вы неправильно вписали значения в форму.")


@router.get('/item/{inventory_number}', summary="Получить вещь из инвентаря")
async def get_inventory_item(request: Request, inventory_number: str):
    item = await DAOTool.get_one(inventory_number=inventory_number)
    return templates.TemplateResponse('inventory_item.html', {
        'request': request,
        'item': item
    })

