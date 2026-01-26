"""
Content Domain Models.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class ContentItem(SQLModel, table=True):
    __tablename__ = "content_items"

    id: str = Field(primary_key=True, max_length=100)
    type: str = Field(max_length=50, default="exercise")
    title: str | None = Field(sa_column=Column(Text))
    level: str | None = Field(max_length=50)
    subject: str | None = Field(max_length=100)
    set_name: str | None = Field(max_length=100)
    year: int | None = Field(default=None)
    lang: str = Field(max_length=10, default="ar")
    md_content: str = Field(sa_column=Column(Text))
    source_path: str | None = Field(max_length=255)
    sha256: str | None = Field(max_length=64)

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


class ContentSolution(SQLModel, table=True):
    __tablename__ = "content_solutions"

    content_id: str = Field(primary_key=True, max_length=100)
    solution_md: str = Field(sa_column=Column(Text))
    steps_json: str | None = Field(sa_column=Column(Text))  # Stores JSON as text
    final_answer: str | None = Field(sa_column=Column(Text))
    verified_by: str | None = Field(max_length=100)

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


class ContentSearch(SQLModel, table=True):
    __tablename__ = "content_search"

    content_id: str = Field(primary_key=True, max_length=100)
    plain_text: str = Field(sa_column=Column(Text))
    # Note: tsvector is database specific (Postgres), so we don't define it here for SQLite compatibility in simplistic tests
    # But migration scripts should add it.
