"""Super migration: Make mission_events.event_type TEXT, add composite index, optional length check, diagnostics.

Revision ID: 20250902_event_type_text_and_index_super
Revises: 0b5107e8283d
Create Date: 2025-09-02
"""

from alembic import op
import sqlalchemy as sa
from contextlib import suppress

revision = "20250902_event_type_text_and_index_super"
down_revision = "0b5107e8283d"
branch_labels = None
depends_on = None

ADD_LENGTH_CHECK = True
LENGTH_LIMIT = 128
CHECK_NAME = "ck_mission_events_event_type_len"
COMPOSITE_INDEX_NAME = "ix_mission_events_mission_created_type"
LEGACY_SINGLE_INDEX = "ix_mission_events_event_type"

def _dialect_name():
    bind = op.get_bind()
    return bind.dialect.name.lower()

def _column_is_already_text(inspector):
    for col in inspector.get_columns("mission_events"):
        if col["name"] == "event_type":
            coltype = col["type"].__class__.__name__.lower()
            if "text" in coltype:
                return True
    return False

def _print_diagnostics():
    bind = op.get_bind()
    dialect = _dialect_name()
    print(f"[event_type migration] Dialect: {dialect}")
    with suppress(Exception):
        res = bind.execute(sa.text(
            "SELECT MAX(char_length(event_type)) AS max_len, COUNT(*) AS total FROM mission_events"
        )).first()
        if res:
            print(f"[event_type migration] Pre-change stats: max_len={res.max_len}, total_rows={res.total}")
    try:
        inspector = sa.inspect(bind)
        for col in inspector.get_columns("mission_events"):
            if col["name"] == "event_type":
                print(f"[event_type migration] Current column type object: {col['type']}")
                break
    except Exception as e:
        print(f"[event_type migration] Could not inspect columns: {e}")

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    _print_diagnostics()

    if not _column_is_already_text(inspector):
        dialect = _dialect_name()
        if dialect == "sqlite":
            with op.batch_alter_table("mission_events") as batch_op:
                batch_op.alter_column(
                    "event_type",
                    type_=sa.Text(),
                    existing_type=sa.String(length=17),
                    existing_nullable=False
                )
        else:
            op.alter_column(
                "mission_events",
                "event_type",
                type_=sa.Text(),
                existing_type=sa.String(length=17),
                existing_nullable=False
            )
        print("[event_type migration] Column altered to TEXT.")
    else:
        print("[event_type migration] NOTE: event_type already TEXT (skipping ALTER).")

    if ADD_LENGTH_CHECK:
        with suppress(Exception):
            existing_checks = bind.execute(sa.text(
                "SELECT conname FROM pg_constraint c "
                "JOIN pg_class t ON c.conrelid = t.oid "
                "WHERE t.relname='mission_events' AND c.contype='c'"
            )).fetchall() if _dialect_name() == "postgresql" else []
            if any(row[0] == CHECK_NAME for row in existing_checks):
                print(f"[event_type migration] CHECK {CHECK_NAME} already exists, skipping.")
            else:
                op.execute(
                    sa.text(
                        f"ALTER TABLE mission_events "
                        f"ADD CONSTRAINT {CHECK_NAME} CHECK (char_length(event_type) <= :limit)"
                    ).bindparams(limit=LENGTH_LIMIT)
                )
                print(f"[event_type migration] Added CHECK constraint {CHECK_NAME} (<= {LENGTH_LIMIT}).")

    with suppress(Exception):
        op.drop_index(LEGACY_SINGLE_INDEX, table_name="mission_events")
        print(f"[event_type migration] Dropped legacy index {LEGACY_SINGLE_INDEX}.")

    try:
        op.create_index(
            COMPOSITE_INDEX_NAME,
            "mission_events",
            ["mission_id", "created_at", "event_type"],
            unique=False
        )
        print(f"[event_type migration] Created composite index {COMPOSITE_INDEX_NAME}.")
    except Exception as e:
        print(f"[event_type migration] Could not create composite index (maybe exists): {e}")

    with suppress(Exception):
        res2 = bind.execute(sa.text(
            "SELECT MAX(char_length(event_type)) AS max_len_after FROM mission_events"
        )).first()
        if res2:
            print(f"[event_type migration] Post-change max length: {res2.max_len_after}")

def downgrade():
    bind = op.get_bind()
    dialect = _dialect_name()
    print("[event_type migration] Starting downgrade...")

    with suppress(Exception):
        op.drop_index(COMPOSITE_INDEX_NAME, table_name="mission_events")
        print(f"[event_type migration] Dropped composite index {COMPOSITE_INDEX_NAME}.")

    if ADD_LENGTH_CHECK and dialect == "postgresql":
        with suppress(Exception):
            op.execute(sa.text(f"ALTER TABLE mission_events DROP CONSTRAINT {CHECK_NAME}"))
            print(f"[event_type migration] Dropped CHECK constraint {CHECK_NAME}.")

    with suppress(Exception):
        op.create_index(
            LEGACY_SINGLE_INDEX,
            "mission_events",
            ["event_type"],
            unique=False
        )
        print(f"[event_type migration] Re-created legacy index {LEGACY_SINGLE_INDEX}.")

    if dialect == "sqlite":
        with op.batch_alter_table("mission_events") as batch_op:
            batch_op.alter_column(
                "event_type",
                type_=sa.String(length=64),
                existing_type=sa.Text(),
                existing_nullable=False
            )
    else:
        op.alter_column(
            "mission_events",
            "event_type",
            type_=sa.String(length=64),
            existing_type=sa.Text(),
            existing_nullable=False
        )
    print("[event_type migration] Downgraded event_type to VARCHAR(64).")