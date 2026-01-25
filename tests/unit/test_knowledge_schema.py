import pytest
from app.core.db_schema import REQUIRED_SCHEMA, _ALLOWED_TABLES

def test_knowledge_tables_in_schema():
    assert "knowledge_nodes" in REQUIRED_SCHEMA
    assert "knowledge_edges" in REQUIRED_SCHEMA
    assert "knowledge_nodes" in _ALLOWED_TABLES
    assert "knowledge_edges" in _ALLOWED_TABLES

def test_knowledge_nodes_structure():
    table = REQUIRED_SCHEMA["knowledge_nodes"]
    columns = table["columns"]
    assert "embedding" in columns
    assert "metadata" in columns

    # Check vector index definition
    indexes = table["indexes"]
    assert "embedding" in indexes
    assert "vector_cosine_ops" in indexes["embedding"]

def test_knowledge_edges_structure():
    table = REQUIRED_SCHEMA["knowledge_edges"]
    columns = table["columns"]
    assert "source_id" in columns
    assert "target_id" in columns
    assert "relation" in columns
