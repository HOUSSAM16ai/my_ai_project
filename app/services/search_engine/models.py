from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class SearchFilters(BaseModel):
    """
    Metadata filters for content search.
    """
    level: Optional[str] = None
    subject: Optional[str] = None
    branch: Optional[str] = None
    set_name: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None
    lang: Optional[str] = None

class SearchRequest(BaseModel):
    """
    Unified search request object.
    """
    q: Optional[str] = None
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: int = 10
    debug_mode: bool = False

class SearchResult(BaseModel):
    """
    Standardized search result.
    """
    model_config = ConfigDict(populate_by_name=True, extra='allow')

    id: str
    title: str
    type: Optional[str] = None
    level: Optional[str] = None
    subject: Optional[str] = None
    branch: Optional[str] = None
    set_name: Optional[str] = Field(None, alias="set") # Alias 'set' to match legacy dict
    year: Optional[int] = None
    lang: Optional[str] = None

    # Extra metadata not strictly in the DB schema but useful for debugging
    score: Optional[float] = None
    strategy: Optional[str] = None
