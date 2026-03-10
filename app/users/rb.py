from pydantic import BaseModel, Field, field_validator, EmailStr
from app.users.dao import DAORole


class RBRegistration(BaseModel):

    username: str
    email: EmailStr
    password: str
    role: str = Field(default='DOCTOR')

    @field_validator('role')
    @classmethod
    async def validate_role(cls, value: str) -> str:
        role = await DAORole.get_one(role=value)
        if not role:
            raise ValueError('Роль, которая выбрана для этого пользователя не существует.')
        return value


class RBLogin(BaseModel):
    username: str
    password: str
