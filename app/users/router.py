from fastapi import APIRouter
from fastapi.responses import RedirectResponse, Response
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from app.users.dao import DAOUser
from app.users.rb import RBRegistration, RBLogin
from app.users.auth import get_password_hash, verify_password, create_access_token, decode_token
from app.users.schemas import AccountResponse


router = APIRouter(prefix="/users", tags=["работа с пользователями"])


@router.get('/', summary="Вывести список пользователей")
async def get_all_users():
    return await DAOUser.get_all()


@router.post('/registration', summary="Зарегистрировать пользователя")
async def create_user(user_info: RBRegistration):
    username = user_info.username
    password = get_password_hash(user_info.password)
    email = user_info.email
    role = await user_info.role

    await DAOUser.create(username=username, password=password, email=email, role=role)
    return RedirectResponse('/users', status_code=301)


@router.post('/login', summary="Войти под пользователем")
async def login_user(response: Response, user_info: RBLogin):
    if await DAOUser.check(username=user_info.username):
        user = await DAOUser.get_one(username=user_info.username)
        if verify_password(user_info.password, user.password):
            access_token = create_access_token({'sub': str(user.id)})
            response.set_cookie(key="users_access_token", value=access_token, httponly=True)
            return {'access_token': access_token, 'refresh_token': None}


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