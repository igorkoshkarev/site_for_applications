import app.database as database
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Text, ForeignKey


class Application(database.Base):
    id: Mapped[database.int_pk]
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    user = relationship('User', back_populates='applications')
