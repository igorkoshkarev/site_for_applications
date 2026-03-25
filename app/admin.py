from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from crudadmin import CRUDAdmin
from crudadmin.admin_interface.model_view import PasswordTransformer

from app.config import settings
from app.mail import start_mail_worker, stop_mail_worker
from app.applications.models import Application, ApplicationStatus
from app.inventory.models import Tool, ToolStatus, Cabinet
from app.users.models import User, Role
from app.users.auth import get_password_hash
from app.database import get_session


class UserCreateSchema(BaseModel):
    username: str
    full_name: str
    password: str
    email: EmailStr | None = None
    phone: str | None = None
    cabinet: str | None = None
    role_name: str


class UserUpdateSchema(BaseModel):
    username: str | None = None
    full_name: str | None = None
    password: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    cabinet: str | None = None
    role_name: str | None = None


class RoleCreateSchema(BaseModel):
    role: str
    russian_name: str | None = None
    css_style_class: str | None = None
    law_create_applications: bool = False
    law_update_applications: bool = False
    law_delete_applications: bool = False
    law_create_users: bool = False
    law_update_users: bool = False
    law_delete_users: bool = False
    law_show_inventory: bool = False
    law_add_inventory: bool = False
    law_use_inventory: bool = False
    law_delete_inventory: bool = False
    law_open_admin_panel: bool = False


class RoleUpdateSchema(BaseModel):
    russian_name: str | None = None
    css_style_class: str | None = None
    law_create_applications: bool | None = None
    law_update_applications: bool | None = None
    law_delete_applications: bool | None = None
    law_create_users: bool | None = None
    law_update_users: bool | None = None
    law_delete_users: bool | None = None
    law_show_inventory: bool | None = None
    law_add_inventory: bool | None = None
    law_use_inventory: bool | None = None
    law_delete_inventory: bool | None = None
    law_open_admin_panel: bool | None = None


class CabinetCreateSchema(BaseModel):
    name: str
    description: str
    floor: int


class CabinetUpdateSchema(BaseModel):
    description: str | None = None
    floor: int | None = None


class ToolCreateSchema(BaseModel):
    inventory_number: str
    name: str
    status: ToolStatus = ToolStatus.in_storage
    cabinet_name: str


class ToolUpdateSchema(BaseModel):
    name: str | None = None
    status: ToolStatus | None = None
    cabinet_name: str | None = None


class ApplicationCreateSchema(BaseModel):
    title: str
    description: str | None = None
    status: ApplicationStatus = ApplicationStatus.is_open
    user_id: int
    performer_id: int | None = None


class ApplicationUpdateSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ApplicationStatus | None = None
    performer_id: int | None = None

# Create admin interface
admin = CRUDAdmin(
    session=get_session,
    SECRET_KEY=settings.ADMIN_SECRET_KEY,
    initial_admin={
        "username": settings.ADMIN_LOGIN,
        "password": settings.ADMIN_PASSWORD
    }
)

admin.add_view(
    model=Role,
    create_schema=RoleCreateSchema,
    update_schema=RoleUpdateSchema,
)
admin.add_view(
    model=Cabinet,
    create_schema=CabinetCreateSchema,
    update_schema=CabinetUpdateSchema,
)
admin.add_view(
    model=User,
    create_schema=UserCreateSchema,
    update_schema=UserUpdateSchema,
    password_transformer=PasswordTransformer(
        password_field="password",
        hashed_field="password",
        hash_function=get_password_hash,
        required_fields=["username", "full_name", "role_name"],
    ),
)
admin.add_view(
    model=Application,
    create_schema=ApplicationCreateSchema,
    update_schema=ApplicationUpdateSchema,
)
admin.add_view(
    model=Tool,
    create_schema=ToolCreateSchema,
    update_schema=ToolUpdateSchema,
)

# Setup FastAPI with proper initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize admin interface
    await admin.initialize()
    start_mail_worker()
    try:
        yield
    finally:
        await stop_mail_worker()
