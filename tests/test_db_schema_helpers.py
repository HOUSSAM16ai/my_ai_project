"""اختبارات مساعدة لمحول مخطط قاعدة البيانات."""

from app.core import db_schema


class _FakeDialect:
    """محاكاة مبسطة لكائن المحرك في الاختبارات."""

    def __init__(self, name: str) -> None:
        self.name = name


class _FakeConnection:
    """محاكاة مبسطة للاتصال مع تحديد اسم المحرك."""

    def __init__(self, name: str) -> None:
        self.dialect = _FakeDialect(name)


def test_to_sqlite_ddl_converts_postgres_types() -> None:
    source = (
        'CREATE TABLE "example"('
        '"id" SERIAL PRIMARY KEY,'
        '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
        '"payload" JSONB,'
        '"ref_id" UUID,'
        '"embedding" vector(1536),'
        '"active" BOOLEAN DEFAULT TRUE,'
        '"archived" BOOLEAN DEFAULT FALSE'
        ")"
    )

    converted = db_schema._to_sqlite_ddl(source)

    assert "INTEGER PRIMARY KEY AUTOINCREMENT" in converted
    assert "TIMESTAMP" in converted
    assert "JSONB" not in converted
    assert "UUID" not in converted
    assert "vector" not in converted
    assert "DEFAULT 1" in converted
    assert "DEFAULT 0" in converted
    assert "CURRENT_TIMESTAMP" in converted


def test_to_sqlite_ddl_strips_unsupported_indexes() -> None:
    hnsw_query = 'CREATE INDEX "ix_demo" ON "demo" USING hnsw("embedding")'
    gin_query = 'CREATE INDEX "ix_demo" ON "demo" USING GIN("payload")'
    mixed_case_query = 'CREATE INDEX "ix_demo" ON "demo" using HnSw("embedding")'

    assert db_schema._to_sqlite_ddl(hnsw_query) == ""
    assert db_schema._to_sqlite_ddl(gin_query) == ""
    assert db_schema._to_sqlite_ddl(mixed_case_query) == ""


def test_to_sqlite_ddl_removes_add_column_if_not_exists() -> None:
    query = 'ALTER TABLE "demo" ADD COLUMN IF NOT EXISTS "new_col" TEXT'

    converted = db_schema._to_sqlite_ddl(query)

    assert "ADD COLUMN IF NOT EXISTS" not in converted
    assert "ADD COLUMN" in converted


def test_infer_index_name_from_query() -> None:
    query = 'CREATE INDEX IF NOT EXISTS "ix_demo_name" ON "demo"("name")'

    assert db_schema._infer_index_name(query) == "ix_demo_name"


def test_infer_index_name_returns_none_for_invalid_sql() -> None:
    query = 'CREATE UNIQUE CONSTRAINT "ix_demo_name" ON "demo"("name")'

    assert db_schema._infer_index_name(query) is None


def test_to_sqlite_ddl_keeps_standard_indexes() -> None:
    query = 'CREATE INDEX "ix_demo" ON "demo"("name")'

    converted = db_schema._to_sqlite_ddl(query)

    assert converted == query


def test_apply_dialect_ddl_respects_sqlite() -> None:
    conn = _FakeConnection("sqlite")
    query = 'ALTER TABLE "demo" ADD COLUMN IF NOT EXISTS "new_col" TEXT'

    converted = db_schema._apply_dialect_ddl(conn, query)

    assert "IF NOT EXISTS" not in converted


def test_apply_dialect_ddl_passthrough_for_postgres() -> None:
    conn = _FakeConnection("postgresql")
    query = 'ALTER TABLE "demo" ADD COLUMN IF NOT EXISTS "new_col" TEXT'

    converted = db_schema._apply_dialect_ddl(conn, query)

    assert converted == query
