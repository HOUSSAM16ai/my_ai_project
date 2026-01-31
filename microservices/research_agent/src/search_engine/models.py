from pydantic import BaseModel, ConfigDict, Field


class SearchFilters(BaseModel):
    """
    Metadata filters for content search.
    """

    level: str | None = None
    subject: str | None = None
    branch: str | None = None
    set_name: str | None = None
    year: int | None = None
    type: str | None = None
    lang: str | None = None


class SearchRequest(BaseModel):
    """
    Unified search request object.
    """

    q: str | None = None
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: int = 10
    debug_mode: bool = False


class SearchResult(BaseModel):
    """
    Standardized search result.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    title: str
    type: str | None = None
    level: str | None = None
    subject: str | None = None
    branch: str | None = None
    set_name: str | None = Field(None, alias="set")  # Alias 'set' to match legacy dict
    year: int | None = None
    lang: str | None = None

    # Extra metadata not strictly in the DB schema but useful for debugging
    score: float | None = None
    strategy: str | None = None
