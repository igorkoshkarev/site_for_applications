from app.database import Base, int_pk, role_law
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Text, ForeignKey


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str]
    email: Mapped[str]
    role: Mapped[int] = mapped_column(ForeignKey('roles.role'), nullable=False)


class Role(Base):
    role: Mapped[str] = mapped_column(primary_key=True, unique=True)
    law_create_applications: Mapped[bool]
    law_update_applications: Mapped[bool]
    law_delete_applications: Mapped[bool]
    law_create_users: Mapped[bool]
    law_update_users: Mapped[bool]
    law_delete_users: Mapped[bool]
    law_show_inventory: Mapped[role_law]
    law_add_inventory: Mapped[role_law]
    law_use_inventory: Mapped[role_law]
    law_delete_inventory: Mapped[role_law]

