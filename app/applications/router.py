from fastapi import APIRouter, Depends
from fastapi.requests import Request
from app.applications.rb import ApplicationSearchFilter, ApplicationPagination, CreateApplicationRB
from typing import Annotated
from app.applications.dao import ApplicationsDAO
from app.utils import get_user_id_from_cookies


router = APIRouter(prefix="/applications", tags=['Работа с заявками'])


@router.get('/', summary='Получить все заявки')
async def get_applications(
    filter: Annotated[ApplicationSearchFilter, Depends(ApplicationSearchFilter)],
    pagination: Annotated[ApplicationPagination, Depends(ApplicationPagination)]):

    applications = await ApplicationsDAO.get_all_with_limit(pagination.limit, 
                                                      pagination.offset,
                                                      **dict(filter))
    
    return applications


@router.post('/create', summary='Создать заявку')
async def create_application(request: Request, application_info: CreateApplicationRB):
    user_id = get_user_id_from_cookies(request)
    await ApplicationsDAO.create(user_id=user_id, **dict(application_info))
    return {'ok': True}
