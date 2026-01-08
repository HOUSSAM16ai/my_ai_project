from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship


class MemoryTagLink(SQLModel, table=True):
    memory_id: UUID = Field(foreign_key="memory.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)

    memories: list["Memory"] = Relationship(back_populates="tags", link_model=MemoryTagLink)


class Memory(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    content: str = Field(index=True)

    tags: list[Tag] = Relationship(back_populates="memories", link_model=MemoryTagLink)
