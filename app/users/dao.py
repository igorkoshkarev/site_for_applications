from app.database import async_session_maker
from sqlalchemy import select
from app.users.models import Role, User


class DAORole:
    @classmethod
    async def get_role_by_name(cls, role: str):
        async with async_session_maker() as session:
            query = select(Role).where(Role.role == role)
            result = await session.execute(query)
            role = result.scalar()
            if not role:
                raise ValueError('Вы пытаетесь получить роль, которой не существует')
            return role
    
    @classmethod
    async def get_role_by_id(cls, role_id: int):
        async with async_session_maker() as session:
            query = select(Role).where(Role.id == role_id)
            result = await session.execute(query)
            role = result.scalar()
            if not role:
                raise ValueError('Вы пытаетесь получить роль, которой не существует')
            return role


class DAOUser:
    @classmethod
    async def get_user_by_username(cls, username: str):
        async with async_session_maker() as session:
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            user = result.scalar()
            if not user:
                raise ValueError('Вы пытаетесь получить пользователя, которого не существует')
            return user
    
    @classmethod
    async def check_username_existance(cls, username: str):
        try:
            await cls.get_user_by_username(username)
        except ValueError:
            return False
        else:
            return True
    
    @classmethod
    async def get_user_by_id(cls, id: str|int):
        id = int(id)
        async with async_session_maker() as session:
            query = select(User).where(User.id == id)
            result = await session.execute(query)
            user = result.scalar()
            if not user:
                raise ValueError('Вы пытаетесь получить пользователя, которого не существует')
            return user