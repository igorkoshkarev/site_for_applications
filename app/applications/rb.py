from pydantic import BaseModel, Field
from app.schemas import SearchFilter, PaginationModel
from typing import Optional


class ApplicationSearchFilter(BaseModel):
    title: Optional[str] = Field(None)


class CreateApplicationRB(BaseModel):
    title: str
    description: str
    