import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.inventory.dao import DAOCabinet
from app.schemas import PaginationModel
from app.users.auth import create_access_token, decode_token, get_password_hash, verify_password
from app.users.dao import DAORole, DAOUser
from app.users.rb import RBLogin, RBRegistration, UserSearchFilter
from app.users.schemas import AccountResponse


router = APIRouter(prefix='/users', tags=['Users'])
templates = Jinja2Templates(directory=str('app/templates'))
logger = logging.getLogger(__name__)


@router.get('/', name='get_all_users', summary='Get users list')
async def get_all_users(
    request: Request,
    pagination: Annotated[PaginationModel, Depends()],
    filter: Annotated[UserSearchFilter, Depends()],
):
    users = await DAOUser.search_users(
        pagination.limit,
        pagination.get_offset(),
        username=filter.name,
        email=filter.name,
        role_name=filter.role_name,
        cabinet=filter.cabinet,
    )
    users_count = await DAOUser.count()
    roles = await DAORole.get_all(columns=['role', 'russian_name'])
    cabinets = await DAOCabinet.get_all(columns=['name'])

    return templates.TemplateResponse('users.html', {
        'request': request,
        'user': request.state.user,
        'users': users,
        'pagination': pagination.get_context(users_count),
        'roles': roles,
        'cabinets': cabinets,
    })


@router.get('/registration', summary='Registration page')
async def registration_page(request: Request):
    cabinets = await DAOCabinet.get_all(columns=['name'])
    return templates.TemplateResponse('registration.html', {
        'request': request,
        'cabinets': cabinets,
    })


@router.post('/registration', summary='Register user')
async def create_user(request: Request, user_info: Annotated[RBRegistration, Form()]):
    user_info.password = get_password_hash(user_info.password)
    role = DAORole.DEFAULT_ROLE
    payload = user_info.model_dump(exclude={'verify_password'})

    try:
        await DAOUser.create(role_name=role, **payload)
    except Exception as exc:
        logger.exception('Failed to register user %s: %s', user_info.username, exc)
        return RedirectResponse('/users/registration', status_code=302)

    return RedirectResponse('/users/login', status_code=302)


@router.get('/login', summary='Login page')
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {
        'request': request,
    })


@router.post('/login', summary='Login as user')
async def login_user(response: Response, user_info: Annotated[RBLogin, Form()]):
    if await DAOUser.check(username=user_info.username):
        user = await DAOUser.get_one(username=user_info.username)
        if verify_password(user_info.password, user['password']):
            access_token = create_access_token({'sub': str(user['id'])})
            redirect = RedirectResponse(f"/users/{user['id']}", status_code=301)
            redirect.set_cookie(key='users_access_token', value=access_token, httponly=True)
            response.set_cookie(key='users_access_token', value=access_token, httponly=True)
            return redirect

    raise HTTPException(status_code=401, detail='Invalid username or password')


@router.get('/logout', summary='Logout user')
async def logout_user():
    response = RedirectResponse('/users/login', status_code=302)
    response.delete_cookie('users_access_token')
    return response


@router.get('/{user_id}', summary='User profile')
async def foreign_account(request: Request, user_id: int):
    user = await DAOUser.get_one(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Page not found')

    return templates.TemplateResponse('user.html', {
        'request': request,
        'user': request.state.user,
        'account': user,
    })
