import json
import os
import sys
from datetime import datetime

# Adjust path to ensure app modules can be imported
sys.path.append(os.getcwd())

from app.services.procedural_knowledge.domain import AuditStatus
from app.services.procedural_knowledge.engine import GraphAuditor
from app.services.procedural_knowledge.scenarios.bac_math_2024 import load_bac_2024_scenario


def main():
    print("----------------------------------------------------------------")
    print("🚀 INITIALIZING PROCEDURAL AI AUDIT SYSTEM (BAC 2024 MODULE) 🚀")
    print("----------------------------------------------------------------")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mode: STRICT_VERIFICATION")
    print("Target: Bac Algérie 2024 - Math - Sc.Exp - Sujet 1 - Ex 1")
    print("----------------------------------------------------------------\n")

    # 1. Load the Knowledge Graph & Rules
    print("➡️  Loading Procedural Graph and Logic Rules...")
    graph, rules = load_bac_2024_scenario()
    print(f"   ✅ Graph Loaded: {len(graph.nodes)} Nodes, {len(graph.relations)} Relations.")
    print(f"   ✅ Logic Protocol: {len(rules)} Procedural Rules Registered.")

    # 2. Initialize the Auditor Engine
    auditor = GraphAuditor(graph)
    for rule in rules:
        auditor.register_rule(rule)

    # 3. Execute the Audit (The "Procedural" Step)
    print("\n➡️  Executing Deep Logic Audit...")
    results = auditor.run_audit()

    # 4. Generate Legendary Report
    final_status = "PASS"
    report_data = []

    for res in results:
        if res.status != AuditStatus.PASS:
            final_status = "FAIL"

        report_data.append({
            "rule_id": res.rule_id,
            "status": res.status.value,
            "message": res.message,
            "evidence": res.evidence,
            "execution_time_ms": round(res.timestamp * 1000, 3) if res.timestamp else 0
        })

    # Output JSON Report
    print("\n📊 FINAL AUDIT REPORT (JSON):")
    print(json.dumps({
        "audit_id": "AUDIT-BAC-2024-001",
        "overall_status": final_status,
        "details": report_data
    }, indent=2, ensure_ascii=False))

    print("\n----------------------------------------------------------------")
    if final_status == "PASS":
        print("✅ SUCCESS: The Procedural Graph is Logically Consistent.")
        print("   Verification Complete. No Fraud/Error Detected.")
    else:
        print("❌ FAILURE: Logic Inconsistencies Detected.")
        sys.exit(1)
    print("----------------------------------------------------------------")

if __name__ == "__main__":
    main()
