import base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Text, ForeignKey
from enum import Enum



class Application(base.Base):
    id: Mapped[base.int_pk]
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)


