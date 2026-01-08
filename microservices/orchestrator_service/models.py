from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, JSON


class Task(SQLModel, table=True):
    """
    نموذج المهمة لقاعدة البيانات.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    description: str = Field(index=True)
    status: str = Field(default="pending")
