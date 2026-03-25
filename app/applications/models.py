import app.database as database
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Text, ForeignKey
from enum import Enum


class ApplicationStatus(str, Enum):
    is_open = "is_open"
    in_process = "in_process"
    is_closed = "is_closed"
    is_confirmed = "is_confirmed"


class Application(database.Base):
    id: Mapped[database.int_pk]
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(server_default=ApplicationStatus.is_open, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    performer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)

    user = relationship('User', foreign_keys=[user_id], back_populates='applications')
    performer = relationship('User', foreign_keys=[performer_id], back_populates="performed_applications")
