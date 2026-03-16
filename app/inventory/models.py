from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from enum import Enum, auto


class Status(str, Enum):
    in_storage: str = auto()
    used: str = auto()
    broken: str = auto()
    used_up: str = auto()


class Tool(Base):
    inventory_number: Mapped[str] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str]
    status: Mapped[Status] = mapped_column(server_default=Status.in_storage)
    cabinet_name: Mapped[str] = mapped_column(ForeignKey('cabinets.name'))

    cabinet = relationship('Cabinet', back_populates='inventory')


class Cabinet(Base):
    name: Mapped[str] = mapped_column(primary_key=True, unique=True)
    description: Mapped[str]
    floor: Mapped[int]

    inventory = relationship('Tool', back_populates='cabinet')