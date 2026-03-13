from pydantic import BaseModel, Field
from typing import Optional, TypeAlias


class SearchFilter(BaseModel):
    name: Optional[str] = Field(None)
    

class Pagination(BaseModel):
    limit: int = Field(10, ge=0)
    offset: int = Field(0, ge=0)
