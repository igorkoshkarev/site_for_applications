from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from app.database import async_session_maker
from app.users.models import User, Role
from app.users.dao import DAORole, DAOUser
from app.users.rb import RBRegistration, RBLogin
from app.users.auth import get_password_hash, verify_password, create_access_token


router = APIRouter(prefix="/users", tags=["работа с пользователями"])

@router.get('/', summary="Вывести список пользователей")
async def get_all_users():
    async with async_session_maker() as session:
        query = select(User)
        result = await session.execute(query)
        return result.scalars().all()


@router.post('/registration', summary="Зарегистрировать пользователя")
async def create_user(user_info: RBRegistration):
    async with async_session_maker() as session:
        username = user_info.username
        password = get_password_hash(user_info.password)
        email = user_info.email
        role = await DAORole.get_role_by_name(await user_info.role)

        user = User(username=username, password=password, email=email, role_id=role.id)
        session.add(user)
        await session.commit()
        return RedirectResponse('/users', status_code=301)


@router.post('/login', summary="Войти под пользователем")
async def create_user(response: Response, user_info: RBLogin):
    if DAOUser.check_username_existance(user_info.username):
        user = await DAOUser.get_user_by_username(user_info.username)
        if verify_password(user_info.password, user.password):
            print(str(user.id))
            access_token = create_access_token({'sub': str(user.id)})
            response.set_cookie(key="users_access_token", value=access_token, httponly=True)
            return {'access_token': access_token, 'refresh_token': None}
