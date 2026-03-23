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
from app.applications.models import ApplicationStatus
from app.users.auth import get_user_id_from_token


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
        'user': request.state.user,
        'applications': applications,
        'filter': filter,
        'pagination': pagination.get_context(len(applications)),
    })


@router.get('/create', summary='страница создания заявки')
async def create_application_page(request: Request):
    return templates.TemplateResponse('create_application.html', {
        'request': request,
        'user': request.state.user
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
        'user': request.state.user,
        'application': application,
        'ApplicationStatus': ApplicationStatus,
    })


@router.get('/{application_id}/accept', summary='Взять заявку на исполнение')
async def accept_application(request: Request, application_id: int):
    await ApplicationsDAO.update_one(application_id, status=ApplicationStatus.in_process, performer_id=get_user_id_from_token(request))
    return RedirectResponse(f'/applications/{application_id}', status_code=302)


@router.get('/{application_id}/close', summary='Закрыть заявку')
async def close_application(request: Request, application_id: int):
    application = await ApplicationsDAO.get_one(id=application_id)
    if application['performer_id'] == get_user_id_from_token(request):
        await ApplicationsDAO.update_one(application_id, status=ApplicationStatus.is_closed)
    return RedirectResponse(f'/applications/{application_id}', status_code=302)
