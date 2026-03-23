from fastapi import APIRouter, Depends, Form
from fastapi.requests import Request
from app.schemas import PaginationModel
from app.applications.rb import ApplicationSearchFilter, CreateApplicationRB
from typing import Annotated
from app.applications.dao import ApplicationsDAO
from app.utils import get_user_id_from_cookies
from fastapi.templating import Jinja2Templates
from typing import Annotated
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/applications", tags=['Работа с заявками'])
templates = Jinja2Templates(directory=str('app/templates'))


@router.get('/', summary='Получить все заявки')
async def get_applications(
    request: Request,
    filter: Annotated[ApplicationSearchFilter, Depends()],
    pagination: Annotated[PaginationModel, Depends()]):

    applications = await ApplicationsDAO.get_all_with_limit(pagination.limit, 
                                                      pagination.get_offset(),
                                                      **dict(filter))
    return templates.TemplateResponse('applications.html', {
        'request': request,
        'applications': applications,
        'filter': filter,
        'pagination': pagination.get_context(len(applications)),
    })


@router.get('/create', summary='страница создания заявки')
async def create_application_page(request: Request):
    return templates.TemplateResponse('create_application.html', {
        'request': request
    })


@router.post('/create', summary='Создать заявку')
async def create_application(request: Request, application_info: Annotated[CreateApplicationRB, Form()]):
    user_id = get_user_id_from_cookies(request)
    await ApplicationsDAO.create(user_id=user_id, **dict(application_info))
    return RedirectResponse('/applications', status_code=301)


@router.get('/{application_id}', summary='Получить заявку')
async def get_application(request: Request, application_id: int):
    application = await ApplicationsDAO.get_one(id=application_id)
    return templates.TemplateResponse('application.html', {
        'request': request,
        'application': application
    })

