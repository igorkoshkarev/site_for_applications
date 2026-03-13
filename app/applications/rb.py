from pydantic import BaseModel, Field
from app.schemas import SearchFilter, Pagination
from typing import Optional


class ApplicationSearchFilter(BaseModel):
    title: Optional[str] = Field(None)


class ApplicationPagination(Pagination):
    ...


class CreateApplicationRB(BaseModel):
    title: str
    description: str
    