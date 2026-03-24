from pydantic import BaseModel, Field
from app.schemas import SearchFilter, PaginationModel
from typing import Optional


class ApplicationSearchFilter(BaseModel):
    title: Optional[str] = Field(None)


class CreateApplicationRB(BaseModel):
    title: str = Field(..., min_length=1, max_length=140, description='Название заявки')
    description: str = Field(..., max_length=1000, description='Описание проблемы')
    