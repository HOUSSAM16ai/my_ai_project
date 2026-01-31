from dataclasses import dataclass


@dataclass
class ContentFilter:
    q: str | None = None
    level: str | None = None
    subject: str | None = None
    branch: str | None = None
    set_name: str | None = None
    year: int | None = None
    type: str | None = None
    lang: str | None = None
    limit: int = 10


@dataclass
class ContentSummary:
    id: str
    title: str | None
    type: str
    level: str | None
    subject: str | None
    branch: str | None
    set_name: str | None
    year: int | None
    lang: str


@dataclass
class ContentDetail:
    id: str
    content_md: str
    solution_md: str | None = None
    metadata: dict[str, object] | None = None
