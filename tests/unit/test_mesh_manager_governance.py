import pytest
from app.services.data_mesh.application.mesh_manager import DataMeshManager
from app.services.data_mesh.domain.models import GovernanceLevel

def test_governance_initialization():
    manager = DataMeshManager()

    # Check that policies are initialized
    assert "quality-standard" in manager.governance_policies
    assert "schema-compatibility" in manager.governance_policies

    # Check Quality Standard Policy content
    quality_policy = manager.governance_policies["quality-standard"]
    assert quality_policy.name == "Data Quality Standard"
    assert quality_policy.level == GovernanceLevel.MANDATORY
    assert len(quality_policy.rules) == 3

    rule_types = {r["type"] for r in quality_policy.rules}
    assert "completeness" in rule_types
    assert "accuracy" in rule_types
    assert "freshness_max_seconds" in rule_types

    # Check Schema Compatibility Policy content
    schema_policy = manager.governance_policies["schema-compatibility"]
    assert schema_policy.name == "Schema Compatibility Policy"
    assert schema_policy.level == GovernanceLevel.MANDATORY
    assert len(schema_policy.rules) == 2

    schema_rule_types = {r["type"] for r in schema_policy.rules}
    assert "compatibility_mode" in schema_rule_types
    assert "breaking_changes" in schema_rule_types
