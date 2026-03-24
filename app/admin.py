from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from crudadmin import CRUDAdmin

from app.config import settings
from app.users.models import User, Role
from app.users.rb import RBRegistration
from app.database import get_session

# Create admin interface
admin = CRUDAdmin(
    session=get_session,
    SECRET_KEY=settings.ADMIN_SECRET_KEY,
    initial_admin={
        "username": settings.ADMIN_LOGIN,
        "password": settings.ADMIN_PASSWORD
    }
)

# Setup FastAPI with proper initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize admin interface
    await admin.initialize()
    yield
