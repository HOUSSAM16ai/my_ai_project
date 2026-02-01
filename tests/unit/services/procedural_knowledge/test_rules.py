from app.services.procedural_knowledge.domain import (
    AuditStatus,
    KnowledgeNode,
    NodeType,
    Relation,
    RelationType,
)
from app.services.procedural_knowledge.engine import (
    ConflictOfInterestRule,
    CycleDetectionRule,
    SuspiciousLocationRule,
)


def test_conflict_of_interest_rule_fail():
    """Test that the rule detects a conflict of interest."""
    nodes = [
        KnowledgeNode(id="t1", type=NodeType.TENDER, label="Tender 1"),
        KnowledgeNode(id="off1", type=NodeType.OFFICIAL, label="Official 1"),
        KnowledgeNode(id="sup1", type=NodeType.SUPPLIER, label="Supplier 1"),
    ]
    relations = [
        Relation(source_id="t1", target_id="off1", type=RelationType.ISSUED_BY),
        Relation(source_id="sup1", target_id="t1", type=RelationType.PARTICIPATED_IN),
        Relation(source_id="off1", target_id="sup1", type=RelationType.RELATED_TO),
    ]

    rule = ConflictOfInterestRule()
    result = rule(nodes, relations)

    assert result.status == AuditStatus.FAIL
    assert result.rule_id == "conflict_of_interest"
    assert len(result.evidence) > 0


def test_conflict_of_interest_rule_pass():
    """Test that the rule passes when there is no conflict."""
    nodes = [
        KnowledgeNode(id="t1", type=NodeType.TENDER, label="Tender 1"),
        KnowledgeNode(id="off1", type=NodeType.OFFICIAL, label="Official 1"),
        KnowledgeNode(id="sup1", type=NodeType.SUPPLIER, label="Supplier 1"),
    ]
    relations = [
        Relation(source_id="t1", target_id="off1", type=RelationType.ISSUED_BY),
        Relation(source_id="sup1", target_id="t1", type=RelationType.PARTICIPATED_IN),
        # No RELATED_TO relation
    ]

    rule = ConflictOfInterestRule()
    result = rule(nodes, relations)

    assert result.status == AuditStatus.PASS
    assert len(result.evidence) == 0


def test_suspicious_location_rule_fail():
    """Test that the rule detects shared addresses."""
    nodes = [
        KnowledgeNode(id="addr1", type=NodeType.ADDRESS, label="123 Fake St"),
        KnowledgeNode(id="comp1", type=NodeType.COMPANY, label="Company A"),
        KnowledgeNode(id="comp2", type=NodeType.COMPANY, label="Company B"),
    ]
    relations = [
        Relation(source_id="comp1", target_id="addr1", type=RelationType.LOCATED_AT),
        Relation(source_id="comp2", target_id="addr1", type=RelationType.LOCATED_AT),
    ]

    rule = SuspiciousLocationRule()
    result = rule(nodes, relations)

    assert result.status == AuditStatus.WARNING
    assert result.rule_id == "suspicious_location"
    assert len(result.evidence) > 0


def test_suspicious_location_rule_pass():
    """Test that the rule passes when addresses are unique."""
    nodes = [
        KnowledgeNode(id="addr1", type=NodeType.ADDRESS, label="123 Fake St"),
        KnowledgeNode(id="addr2", type=NodeType.ADDRESS, label="456 Real St"),
        KnowledgeNode(id="comp1", type=NodeType.COMPANY, label="Company A"),
        KnowledgeNode(id="comp2", type=NodeType.COMPANY, label="Company B"),
    ]
    relations = [
        Relation(source_id="comp1", target_id="addr1", type=RelationType.LOCATED_AT),
        Relation(source_id="comp2", target_id="addr2", type=RelationType.LOCATED_AT),
    ]

    rule = SuspiciousLocationRule()
    result = rule(nodes, relations)

    assert result.status == AuditStatus.PASS


def test_cycle_detection_rule_fail():
    """Test that the rule detects ownership cycles."""
    nodes = [
        KnowledgeNode(id="c1", type=NodeType.COMPANY, label="Company 1"),
        KnowledgeNode(id="c2", type=NodeType.COMPANY, label="Company 2"),
        KnowledgeNode(id="c3", type=NodeType.COMPANY, label="Company 3"),
    ]
    relations = [
        Relation(source_id="c1", target_id="c2", type=RelationType.OWNS),
        Relation(source_id="c2", target_id="c3", type=RelationType.OWNS),
        Relation(source_id="c3", target_id="c1", type=RelationType.OWNS),
    ]

    rule = CycleDetectionRule()
    result = rule(nodes, relations)

    assert result.status == AuditStatus.FAIL
    assert result.rule_id == "shell_company_cycle"
    assert len(result.evidence) > 0


def test_cycle_detection_rule_pass():
    """Test that the rule passes when there are no cycles."""
    nodes = [
        KnowledgeNode(id="c1", type=NodeType.COMPANY, label="Company 1"),
        KnowledgeNode(id="c2", type=NodeType.COMPANY, label="Company 2"),
        KnowledgeNode(id="c3", type=NodeType.COMPANY, label="Company 3"),
    ]
    relations = [
        Relation(source_id="c1", target_id="c2", type=RelationType.OWNS),
        Relation(source_id="c2", target_id="c3", type=RelationType.OWNS),
    ]

    rule = CycleDetectionRule()
    result = rule(nodes, relations)

    assert result.status == AuditStatus.PASS
