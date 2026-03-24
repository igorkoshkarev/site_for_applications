from app.database import Base, int_pk, role_law
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Text, ForeignKey


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    cabinet: Mapped[str] = mapped_column(ForeignKey('cabinets.name'), nullable=True)
    role_name: Mapped[int] = mapped_column(ForeignKey('roles.role'), nullable=False)

    role = relationship('Role', back_populates='users')
    applications = relationship("Application", foreign_keys='[Application.user_id]', back_populates="user")
    performed_applications = relationship('Application', foreign_keys='[Application.performer_id]', back_populates='performer')


class Role(Base):
    role: Mapped[str] = mapped_column(primary_key=True, unique=True)
    russian_name: Mapped[str] = mapped_column(nullable=True)
    css_style_class: Mapped[str] = mapped_column(nullable=True)
    law_create_applications: Mapped[role_law]
    law_update_applications: Mapped[role_law]
    law_delete_applications: Mapped[role_law]
    law_create_users: Mapped[role_law]
    law_update_users: Mapped[role_law]
    law_delete_users: Mapped[role_law]
    law_show_inventory: Mapped[role_law]
    law_add_inventory: Mapped[role_law]
    law_use_inventory: Mapped[role_law]
    law_delete_inventory: Mapped[role_law]

    users = relationship("User", back_populates="role")
