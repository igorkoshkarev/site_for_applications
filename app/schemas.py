from pydantic import BaseModel, Field
from typing import Optional, TypeAlias, Annotated
from math import ceil

str_search_filter = Annotated[Optional[str], Field(None)]

class SearchFilter(BaseModel):
    name: Optional[str] = Field(None)
    

class PaginationModel(BaseModel):
    limit: int = Field(10, ge=0)
    page: int = Field(1, ge=1)

    def get_context(self, total: int) -> dict:
        pages = ceil(total / self.limit)
        context = {
            'total': total,
            'page': self.page,
            'limit': self.limit,
            'pages': pages,
            'next_page': self.page+1 if pages >= self.page+1 else self.page,
            'prev_page': self.page-1 if self.page > 1 else self.page
        }
        return context
    
    def get_offset(self):
        return self.limit * (self.page-1)