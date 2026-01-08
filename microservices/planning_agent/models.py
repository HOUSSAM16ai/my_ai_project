from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, JSON


class Plan(SQLModel, table=True):
    """
    نموذج الخطة لقاعدة البيانات.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    goal: str = Field(index=True)
    steps: list[str] = Field(default_factory=list, sa_type=JSON)
