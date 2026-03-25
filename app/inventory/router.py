import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.inventory.dao import DAOCabinet, DAOTool
from app.inventory.models import ToolStatus
from app.inventory.rb import CreateInventoryRB, InventorySearchFilter
from app.schemas import PaginationModel


router = APIRouter(prefix='/inventory', tags=['Inventory'])
templates = Jinja2Templates(directory='app/templates')
logger = logging.getLogger(__name__)


@router.get('/item/{inventory_number}/equip', summary='Equip inventory item')
async def equip_inventory_item(inventory_number: str):
    try:
        await DAOTool.update_one(inventory_number, **{'status': ToolStatus.used})
    except Exception as exc:
        logger.exception('Failed to equip inventory item %s: %s', inventory_number, exc)
        raise HTTPException(status_code=404, detail='Item not found')

    response = RedirectResponse('/inventory', status_code=302)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@router.get('/item/{inventory_number}/put', summary='Put inventory item back')
async def put_inventory_item(inventory_number: str):
    try:
        await DAOTool.update_one(inventory_number, **{'status': ToolStatus.in_storage})
    except Exception as exc:
        logger.exception('Failed to put inventory item %s: %s', inventory_number, exc)
        raise HTTPException(status_code=404, detail='Item not found')

    response = RedirectResponse('/inventory', status_code=302)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@router.get('/', summary='Get all inventory')
async def get_all_inventory(
    request: Request,
    pagination: Annotated[PaginationModel, Depends()],
    filter: Annotated[InventorySearchFilter, Depends()],
):
    total = await DAOTool.count()
    inventory = await DAOTool.get_all_with_limit(
        pagination.limit,
        pagination.get_offset(),
        **dict(filter),
    )
    return templates.TemplateResponse('inventory.html', {
        'user': request.state.user,
        'request': request,
        'inventory': inventory,
        'status': ToolStatus,
        'pagination': pagination.get_context(total),
    })


@router.get('/create', summary='Create inventory page')
async def create_inventory_page(request: Request):
    cabinets = await DAOCabinet.get_all(columns=['name'])
    return templates.TemplateResponse('create_inventory_item.html', {
        'user': request.state.user,
        'request': request,
        'cabinets': cabinets,
        'status': ToolStatus,
    })


@router.post('/create', summary='Create inventory item')
async def create_inventory(request: Request, inventory_info: Annotated[CreateInventoryRB, Form()]):
    if not await DAOCabinet.check(name=inventory_info.cabinet_name):
        raise HTTPException(status_code=401, detail='Cabinet not found')

    try:
        await DAOTool.create(**dict(inventory_info))
    except Exception as exc:
        logger.exception('Failed to create inventory item %s: %s', inventory_info.inventory_number, exc)
        raise HTTPException(status_code=401, detail='Invalid inventory item data')

    return RedirectResponse('/inventory', status_code=301)


@router.get('/item/{inventory_number}', summary='Get inventory item')
async def get_inventory_item(request: Request, inventory_number: str):
    item = await DAOTool.get_one(inventory_number=inventory_number)
    if item:
        return templates.TemplateResponse('inventory_item.html', {
            'request': request,
            'user': request.state.user,
            'item': item,
        })
    raise HTTPException(status_code=404, detail='Item not found')
