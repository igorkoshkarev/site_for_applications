from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from app.database import async_session_maker
from app.users.models import User, Role
from app.users.dao import DAORole, DAOUser
from app.users.rb import RBRegistration, RBLogin


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
        role = await DAORole.get_role_by_name(await user_info.role)
        user = User(username=username, role_id=role.id)
        session.add(user)
        await session.commit()
        return RedirectResponse('/users', status_code=301)
