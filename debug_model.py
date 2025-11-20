from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    missions: Mapped[List["Mission"]] = relationship(back_populates="user")

class Mission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: Mapped["User"] = relationship(back_populates="missions")

print("Models defined successfully")
