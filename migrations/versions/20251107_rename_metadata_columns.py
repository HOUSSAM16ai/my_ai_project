"""Rename metadata to meta_data to avoid SQLAlchemy reserved name

Revision ID: 20251107_rename_metadata
Revises: 20251107_cosmic_security
Create Date: 2025-11-07 11:16:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251107_rename_metadata"
down_revision = "20251107_cosmic_security"
branch_labels = None
depends_on = None


def upgrade():
    """Rename metadata columns to meta_data in all cosmic tables."""

    # List of tables that have metadata column
    tables = [
        "existential_nodes",
        "consciousness_signatures",
        "cosmic_ledger",
        "seces",
        "existential_protocols",
        "cosmic_governance_councils",
        "existential_transparency_logs",
    ]

    # Rename metadata to meta_data in each table
    for table_name in tables:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.alter_column("metadata", new_column_name="meta_data")


def downgrade():
    """Revert meta_data columns back to metadata."""

    # List of tables that have meta_data column
    tables = [
        "existential_nodes",
        "consciousness_signatures",
        "cosmic_ledger",
        "seces",
        "existential_protocols",
        "cosmic_governance_councils",
        "existential_transparency_logs",
    ]

    # Rename meta_data back to metadata in each table
    for table_name in tables:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.alter_column("meta_data", new_column_name="metadata")
