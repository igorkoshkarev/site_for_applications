from app.database import Base, int_pk
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Text, ForeignKey


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str]
    email: Mapped[str]
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False)


class Role(Base):
    id: Mapped[int_pk]
    role: Mapped[str]
    law_create_applications: Mapped[bool]
    law_update_applications: Mapped[bool]
    law_delete_applications: Mapped[bool]
    law_create_users: Mapped[bool]
    law_update_users: Mapped[bool]
    law_delete_users: Mapped[bool]

