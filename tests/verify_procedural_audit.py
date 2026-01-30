"""
Verification Script for Procedural AI & Fraud Detection.
------------------------------------------------------
This script constructs a mock Knowledge Graph representing a fraud scenario
and verifies that the Procedural Engine detects the issues.
"""

import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.procedural_knowledge.domain import (
    AuditStatus,
    KnowledgeNode,
    NodeType,
    ProceduralGraph,
    Relation,
    RelationType,
)
from app.services.procedural_knowledge.engine import (
    ConflictOfInterestRule,
    CycleDetectionRule,
    GraphAuditor,
    SuspiciousLocationRule,
)


def verify_fraud_detection():
    print("🚀 Starting Procedural AI Verification...")

    # 1. Build Mock Graph (The Scenario)
    graph = ProceduralGraph()

    # Official (Corrupt)
    official = KnowledgeNode(id="off_1", type=NodeType.OFFICIAL, label="Ahmed Official")
    graph.add_node(official)

    # Tender
    tender = KnowledgeNode(id="tend_1", type=NodeType.TENDER, label="Road Project 2024")
    graph.add_node(tender)

    # Supplier (Corrupt)
    supplier = KnowledgeNode(id="supp_1", type=NodeType.SUPPLIER, label="Bad Company SARL")
    graph.add_node(supplier)

    # Address (Shared)
    address = KnowledgeNode(id="addr_1", type=NodeType.ADDRESS, label="123 Suspicious St")
    graph.add_node(address)

    # Supplier 2 (Shell Company sharing address)
    supplier2 = KnowledgeNode(id="supp_2", type=NodeType.SUPPLIER, label="Shell Corp")
    graph.add_node(supplier2)

    # Relations
    # 1. Official issued Tender
    graph.add_relation(Relation(source_id="tend_1", target_id="off_1", type=RelationType.ISSUED_BY))

    # 2. Supplier participated in Tender
    graph.add_relation(
        Relation(source_id="supp_1", target_id="tend_1", type=RelationType.PARTICIPATED_IN)
    )

    # 3. Conflict: Official related to Supplier (Hidden connection)
    graph.add_relation(
        Relation(source_id="off_1", target_id="supp_1", type=RelationType.RELATED_TO)
    )

    # 4. Suspicious Location: Both suppliers at same address
    graph.add_relation(
        Relation(source_id="supp_1", target_id="addr_1", type=RelationType.LOCATED_AT)
    )
    graph.add_relation(
        Relation(source_id="supp_2", target_id="addr_1", type=RelationType.LOCATED_AT)
    )

    # 2. Initialize Auditor
    auditor = GraphAuditor(graph)
    auditor.register_rule(ConflictOfInterestRule())
    auditor.register_rule(SuspiciousLocationRule())
    auditor.register_rule(CycleDetectionRule())

    # 3. Run Audit
    print("🔍 Running Audit Rules...")
    results = auditor.run_audit()

    # 4. Verify Results
    failures = 0
    passed = True

    for res in results:
        print(f"   Rule: {res.rule_id} -> {res.status.value}")
        if res.status != AuditStatus.PASS:
            failures += 1
            print(f"      Msg: {res.message}")
            for ev in res.evidence:
                print(f"      Evidence: {ev}")

    # Check Conflict of Interest
    coi = next((r for r in results if r.rule_id == "conflict_of_interest"), None)
    if not coi or coi.status != AuditStatus.FAIL:
        print("❌ FAILED: Conflict of Interest not detected!")
        passed = False
    else:
        print("✅ PASSED: Conflict of Interest detected.")

    # Check Suspicious Location
    loc = next((r for r in results if r.rule_id == "suspicious_location"), None)
    if not loc or loc.status != AuditStatus.WARNING:
        print("❌ FAILED: Suspicious Location not detected!")
        passed = False
    else:
        print("✅ PASSED: Suspicious Location detected.")

    if passed:
        print("\n✨ Verification Successful! The Agent successfully detected fraud patterns.")
    else:
        print("\n💥 Verification Failed.")
        sys.exit(1)


if __name__ == "__main__":
    verify_fraud_detection()
