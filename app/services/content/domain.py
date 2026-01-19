from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class ContentFilter:
    q: Optional[str] = None
    level: Optional[str] = None
    subject: Optional[str] = None
    branch: Optional[str] = None
    set_name: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None
    lang: Optional[str] = None
    limit: int = 10

@dataclass
class ContentSummary:
    id: str
    title: Optional[str]
    type: str
    level: Optional[str]
    subject: Optional[str]
    branch: Optional[str]
    set_name: Optional[str]
    year: Optional[int]
    lang: str

@dataclass
class ContentDetail:
    id: str
    content_md: str
    solution_md: Optional[str] = None
    metadata: Optional[Dict[str, object]] = None
