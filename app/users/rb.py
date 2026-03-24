from pydantic import BaseModel, Field, field_validator, EmailStr, model_validator
from app.schemas import str_search_filter
import re


class UserSearchFilter(BaseModel):
    name: str_search_filter
    role_name: str_search_filter
    cabinet: str_search_filter


class RBRegistration(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, description='Никнейм пользователя')
    full_name: str = Field(..., min_length=1, max_length=30, description='Полное имя пользователя')
    email: EmailStr = Field(..., description='Email пользователя')
    phone: str = Field(..., description='Рабочий телефон пользователя')
    cabinet: str|None = Field(..., description='Кабинет пользователя')
    password: str = Field(..., min_length=8, max_length=30, description='Пароль пользователя')
    verify_password: str  = Field(..., min_length=8, max_length=30, description='Подтверждение пароля пользователя')

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        re_pattern = r'[\+]?[\d]{7,11}'
        if re.match(re_pattern, phone):
            return phone
        raise ValueError('Вы неправильно ввели телефон.')
    
    @field_validator('password')
    def validate_password(cls, password: str) -> str:
        if not(s.isalhpa() for s in password):
            raise ValueError('Пароль не содержит буквенных символов')
        if not any(s.isupper() for s in password):
            raise ValueError('Пароль не имеет большую букву')
        if not any(s.isdigit() for s in password):
            raise ValueError('Пароль не содержит цифр')
        return password

    @model_validator(mode='after')
    def validate_password(self):
        if self.password != self.verify_password:
            raise ValueError('Пароли не совпадают')
        
        return self



class RBLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, description='Никнейм пользователя')
    password: str = Field(..., min_length=8, max_length=30, description='Пароль пользователя')
