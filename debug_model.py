from __future__ import annotations

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    missions: Mapped[list[Mission]] = relationship(back_populates="user")

class Mission(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: Mapped[User] = relationship(back_populates="missions")

print("Models defined successfully")
