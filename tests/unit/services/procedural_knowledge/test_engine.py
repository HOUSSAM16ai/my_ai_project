from unittest.mock import MagicMock, patch

import pytest
from app.services.procedural_knowledge.domain import (
    AuditResult,
    AuditStatus,
    NodeType,
    ProceduralGraph,
    RelationType,
)
from app.services.procedural_knowledge.engine import GraphAuditor, GraphBuilder


# --- GraphBuilder Tests ---

def test_graph_builder_valid_structure():
    """Test building a graph from valid dictionary structure."""
    data = {
        "nodes": [
            {"id": "n1", "type": "entity", "label": "Node 1"},
            {"id": "n2", "type": "entity", "label": "Node 2"},
        ],
        "relations": [
            {"source_id": "n1", "target_id": "n2", "type": "contains"}
        ],
    }
    graph = GraphBuilder.from_structure(data)

    assert len(graph.nodes) == 2
    assert len(graph.relations) == 1
    assert graph.nodes["n1"].label == "Node 1"
    assert graph.relations[0].type == RelationType.CONTAINS


def test_graph_builder_invalid_node_ignored():
    """Test that invalid nodes are ignored (logged as warning) and don't crash the builder."""
    data = {
        "nodes": [
            {"id": "n1", "type": "entity", "label": "Valid Node"},
            {"id": "n2", "type": "invalid_type", "label": "Invalid Node"},  # Assuming enum validation
             # Missing 'type' or 'id' would raise ValidationError from Pydantic
            {"id": "n3"},
        ],
        "relations": [],
    }

    # We expect warnings, but the valid node should be added.
    graph = GraphBuilder.from_structure(data)

    # Only n1 should be present. n2 fails enum validation, n3 fails missing field.
    assert len(graph.nodes) == 1
    assert "n1" in graph.nodes
    assert graph.nodes["n1"].label == "Valid Node"


def test_graph_builder_invalid_relation_ignored():
    """Test that invalid relations are ignored."""
    data = {
        "nodes": [{"id": "n1", "type": "entity", "label": "Node 1"}],
        "relations": [
            {"source_id": "n1", "target_id": "n2"}, # Missing type
        ],
    }
    graph = GraphBuilder.from_structure(data)
    assert len(graph.relations) == 0


# --- GraphAuditor Tests ---

def test_auditor_register_rule():
    """Test registering rules."""
    graph = ProceduralGraph()
    auditor = GraphAuditor(graph)

    mock_rule = MagicMock()
    auditor.register_rule(mock_rule)

    assert len(auditor.rules) == 1
    assert auditor.rules[0] == mock_rule


def test_auditor_run_audit_success():
    """Test running audit with passing rules."""
    graph = ProceduralGraph()
    auditor = GraphAuditor(graph)

    # Create a mock rule that returns a Pass result
    mock_rule = MagicMock()
    expected_result = AuditResult(
        rule_id="test_rule",
        status=AuditStatus.PASS,
        message="Test passed",
        evidence=[]
    )
    mock_rule.return_value = expected_result

    auditor.register_rule(mock_rule)
    results = auditor.run_audit()

    assert len(results) == 1
    assert results[0] == expected_result
    mock_rule.assert_called_once()


def test_auditor_run_audit_failure_logging():
    """Test that failed audits are logged correctly."""
    graph = ProceduralGraph()
    auditor = GraphAuditor(graph)

    mock_rule = MagicMock()
    failure_result = AuditResult(
        rule_id="test_fail",
        status=AuditStatus.FAIL,
        message="Test failed",
        evidence=["ev1"]
    )
    mock_rule.return_value = failure_result
    auditor.register_rule(mock_rule)

    with patch("app.services.procedural_knowledge.engine.logger") as mock_logger:
        results = auditor.run_audit()

        assert len(results) == 1
        assert results[0].status == AuditStatus.FAIL
        # Verify logger.warning was called for failure
        mock_logger.warning.assert_called()


def test_auditor_run_audit_exception_handling():
    """Test that exceptions in rules are caught and returned as failures."""
    graph = ProceduralGraph()
    auditor = GraphAuditor(graph)

    mock_rule = MagicMock()
    mock_rule.side_effect = ValueError("Something went wrong")

    auditor.register_rule(mock_rule)

    with patch("app.services.procedural_knowledge.engine.logger") as mock_logger:
        results = auditor.run_audit()

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "unknown_error"
        assert result.status == AuditStatus.FAIL
        assert "Something went wrong" in result.message
        # Verify logger.error was called
        mock_logger.error.assert_called()
