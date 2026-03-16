from pydantic import BaseModel, Field, field_validator, EmailStr
from app.schemas import str_search_filter


class UserSearchFilter(BaseModel):
    name: str_search_filter
    role_name: str_search_filter
    cabinet: str_search_filter


class RBRegistration(BaseModel):
    username: str
    email: EmailStr
    phone: str
    cabinet: str
    password: str
    verify_password: str


class RBLogin(BaseModel):
    username: str
    password: str
