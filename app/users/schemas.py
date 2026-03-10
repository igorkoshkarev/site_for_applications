from pydantic import BaseModel, EmailStr


class AccountResponse(BaseModel):

    username: str
    email: EmailStr
    role: str

