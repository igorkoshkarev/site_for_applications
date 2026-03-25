import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas import str_search_filter


class UserSearchFilter(BaseModel):
    name: str_search_filter
    role_name: str_search_filter
    cabinet: str_search_filter


class RBRegistration(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, description='Username')
    full_name: str = Field(..., min_length=1, max_length=30, description='Full name')
    email: EmailStr = Field(..., description='User email')
    phone: str = Field(..., description='Work phone')
    cabinet: str | None = Field(..., description='User cabinet')
    password: str = Field(..., min_length=8, max_length=30, description='User password')
    verify_password: str = Field(..., min_length=8, max_length=30, description='Password confirmation')

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        re_pattern = r'[\+]?[\d]{7,11}'
        if re.match(re_pattern, phone):
            return phone
        raise ValueError('Invalid phone number format')

    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not any(s.isalpha() for s in password):
            raise ValueError('Password must contain letters')
        if not any(s.isupper() for s in password):
            raise ValueError('Password must contain an uppercase letter')
        if not any(s.isdigit() for s in password):
            raise ValueError('Password must contain digits')
        return password

    @model_validator(mode='after')
    def validate_password_match(self):
        if self.password != self.verify_password:
            raise ValueError('Passwords do not match')
        return self


class RBLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, description='Username')
    password: str = Field(..., min_length=8, max_length=30, description='User password')
