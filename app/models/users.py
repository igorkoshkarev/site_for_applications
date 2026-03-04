import base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Text
from enum import Enum


class Role(str, Enum):
    ADMIN = 'admin'
    PROGRAMMER = 'programmer'
    DOCTOR = 'doctor'


class User(base.Base):
    id: Mapped[base.int_pk]
    username: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role]


