class ContentSearchQuery:
    """بناء استعلام SQL للبحث في المحتوى."""

    def __init__(self) -> None:
        self.select_clause = (
            "SELECT i.id, i.title, i.type, i.level, i.subject, i.branch, "
            "i.set_name, i.year, i.lang, i.md_content "
        )
        self.from_clause = (
            "FROM content_items i LEFT JOIN content_search cs ON i.id = cs.content_id"
        )
        self.where_clauses: list[str] = ["1=1"]
        self.order_clause = "ORDER BY i.year DESC NULLS LAST, i.id ASC"
        self.limit_clause = ""
        self.params: dict[str, object] = {}

    def add_text_search(self, q: str | None) -> "ContentSearchQuery":
        if not q:
            return self
        terms = [term for term in q.split() if term.strip()]
        term_clauses: list[str] = []
        for index, term in enumerate(terms):
            title_key = f"tq_{index}"
            body_key = f"bq_{index}"
            term_clauses.append(f"(i.title LIKE :{title_key} OR cs.plain_text LIKE :{body_key})")
            like_value = f"%{term}%"
            self.params[title_key] = like_value
            self.params[body_key] = like_value

        if term_clauses:
            self.where_clauses.append(" AND ".join(term_clauses))
        return self

    def add_id_filter(self, content_ids: list[str] | None) -> "ContentSearchQuery":
        if not content_ids:
            return self
        placeholders: list[str] = []
        for index, content_id in enumerate(content_ids):
            key = f"cid_{index}"
            placeholders.append(f":{key}")
            self.params[key] = content_id
        self.where_clauses.append(f"i.id IN ({', '.join(placeholders)})")
        return self

    def add_filter(self, field: str, value: object) -> "ContentSearchQuery":
        if value is not None:
            key = field.rsplit(".", maxsplit=1)[-1]  # Simple key generation
            # Avoid collision if field is used multiple times (unlikely here but safe practice)
            if key in self.params:
                key = f"{key}_{len(self.params)}"

            self.where_clauses.append(f"{field} = :{key}")
            self.params[key] = value
        return self

    def set_limit(self, limit: int) -> "ContentSearchQuery":
        self.limit_clause = "LIMIT :limit"
        self.params["limit"] = limit
        return self

    def build(self) -> tuple[str, dict[str, object]]:
        where_str = " AND ".join(self.where_clauses)
        query = f"{self.select_clause} {self.from_clause} WHERE {where_str} {self.order_clause} {self.limit_clause}"
        return query, self.params
