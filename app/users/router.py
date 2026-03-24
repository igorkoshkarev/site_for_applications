from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse, Response
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from app.users.dao import DAOUser, DAORole
from app.inventory.dao import DAOCabinet
from app.users.rb import RBRegistration, RBLogin
from app.users.auth import get_password_hash, verify_password, create_access_token, decode_token
from app.users.schemas import AccountResponse
from fastapi.templating import Jinja2Templates
from app.schemas import PaginationModel
from typing import Annotated
from app.users.rb import UserSearchFilter


router = APIRouter(prefix="/users", tags=["работа с пользователями"])
templates = Jinja2Templates(directory=str('app/templates'))


@router.get('/', name="get_all_users", summary="Вывести список пользователей")
async def get_all_users(request: Request, pagination: Annotated[PaginationModel, Depends()], filter: Annotated[UserSearchFilter, Depends()]):
    users = await DAOUser.search_users(pagination.limit, pagination.get_offset(), username=filter.name, email=filter.name, role_name=filter.role_name, cabinet=filter.cabinet)
    users_count = await DAOUser.count()
    roles = await DAORole.get_all(columns=['role', 'russian_name'])
    cabinets = await DAOCabinet.get_all(columns=['name'])

    print(request.state.user)

    return templates.TemplateResponse('users.html', {
            'request': request,
            'user': request.state.user,
            'users': users,
            'pagination': pagination.get_context(users_count),
            'roles': roles,
            'cabinets': cabinets
    })

@router.get('/registration', summary="Страница регистрации пользователя")
async def registration_page(request: Request):
    cabinets = await DAOCabinet.get_all(columns=['name'])
    return templates.TemplateResponse('registration.html', {
        'request': request,
        'cabinets': cabinets
    })


@router.post('/registration', summary="Зарегистрировать пользователя")
async def create_user(request: Request, user_info: Annotated[RBRegistration, Form()]): 
    username = user_info.username
    user_info.password = get_password_hash(user_info.password)
    full_name = user_info.full_name
    phone = user_info.phone
    email = user_info.email
    cabinet = user_info.cabinet
    role = DAORole.DEFAULT_ROLE
    try:
        await DAOUser.create(role_name=role, **dict(user_info))
    except:
        return RedirectResponse('/users/registration', status_code=302)
    else:
        return RedirectResponse('/users/login', status_code=302)


@router.get('/login', summary="Страница входа")
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {
        'request': request
    })


@router.post('/login', summary="Войти под пользователем")
async def login_user(response: Response, user_info: Annotated[RBLogin, Form()]):
    if await DAOUser.check(username=user_info.username):
        user = await DAOUser.get_one(username=user_info.username)
        if verify_password(user_info.password, user['password']):
            access_token = create_access_token({'sub': str(user['id'])})
            r = RedirectResponse(f'/users/{user['id']}', status_code=301)
            r.set_cookie(key="users_access_token", value=access_token, httponly=True)
            response.set_cookie(key="users_access_token", value=access_token, httponly=True)
            return r


@router.get('/account', summary="Профиль пользователя")
async def account(request: Request):
    token = request.cookies.get('users_access_token')
    if token:
        decoded_token = decode_token(token)
        user = await DAOUser.get_one(id=int(decoded_token['sub']))
        response = AccountResponse(username=user.username, 
                                   email=user.email, 
                                   role=user.role)
        return response
    raise HTTPException(status_code=422, detail="Вы не зашли под пользователем.")


@router.get('/{user_id}', summary="Профиль пользователя")
async def foreign_account(request: Request, user_id: int):
    user = await DAOUser.get_one(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail='page not found')
    return templates.TemplateResponse('user.html', {
            'request': request,
            'user': request.state.user,
            'account': user
    })