from typing import Optional

from pydantic import BaseModel, Field


class ApplicationSearchFilter(BaseModel):
    title: Optional[str] = Field(None)


class CreateApplicationRB(BaseModel):
    title: str = Field(..., min_length=1, max_length=140, description="Название заявки")
    description: str = Field(..., max_length=1000, description="Описание проблемы")


class ApplicationFeedbackRB(BaseModel):
    feedback: str = Field(..., min_length=3, max_length=2000, description="Отзыв заявителя по выполненной заявке")
