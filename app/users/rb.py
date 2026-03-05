from pydantic import BaseModel, Field, field_validator
from app.users.dao import DAORole
from app.users.models import Role
from app.database import async_session_maker
from sqlalchemy import select


class RBRegistration(BaseModel):

    username: str
    role: str = Field(default='Doctor')

    @field_validator('role')
    @classmethod
    async def validate_role(cls, value: str) -> str:
        role = await DAORole.get_role_by_name(value)
        if not role:
            raise ValueError('Роль, которая выбрана для этого пользователя не существует.')
        return value


class RBLogin(BaseModel):
    username: str
