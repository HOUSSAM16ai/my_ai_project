"""
عقدة المدقق الإجرائي (Procedural Auditor Node).
---------------------------------------------
تقوم هذه العقدة بتحليل السياق، بناء رسم بياني للعلاقات،
وتنفيذ قواعد منطقية لكشف الاحتيال أو التحقق من الامتثال.
"""

import json
import logging
import uuid
from datetime import datetime

from langchain_core.messages import AIMessage

from app.core.ai_gateway import AIClient
from app.services.chat.graph.state import AgentState
from app.services.procedural_knowledge.domain import (
    AuditStatus,
    ComplianceReport,
)
from app.services.procedural_knowledge.engine import (
    ConflictOfInterestRule,
    CycleDetectionRule,
    GraphAuditor,
    GraphBuilder,
    SuspiciousLocationRule,
)

logger = logging.getLogger(__name__)


class ProceduralAuditorNode:
    """
    الوكيل المتخصص في التدقيق الإجرائي وكشف الاحتيال.
    """

    SYSTEM_PROMPT = """
You are the **Procedural Auditor**, a specialized AI agent for fraud detection and compliance verification in Algerian Procurement contexts.

Your goal is to extract a **Knowledge Graph** from the provided text to check for:
1. Conflict of Interest (e.g., Official related to Supplier).
2. Shell Companies (Circular Ownership).
3. Suspicious Locations (Shared Addresses).

**Instructions:**
- Analyze the user's input and any gathered research.
- Identify Entities: Suppliers, Tenders, Officials, Companies, Addresses.
- Identify Relations: OWNS, PARTICIPATED_IN, WON, ISSUED_BY, LOCATED_AT, RELATED_TO.
- Output a strictly valid JSON object representing the graph.

**JSON Format (Strict):**
{
    "nodes": [
        {"id": "comp_a", "type": "company", "label": "Company A"},
        {"id": "addr_1", "type": "address", "label": "123 Main St"}
    ],
    "relations": [
        {"source_id": "comp_a", "target_id": "addr_1", "type": "located_at", "metadata": {}}
    ]
}

Valid Node Types: supplier, tender, contract, invoice, official, company, address, bank_account.
Valid Relation Types: owns, participated_in, won, issued_by, located_at, related_to, transferred_to, signed_by.
"""

    @staticmethod
    async def run_audit(state: AgentState, ai_client: AIClient) -> dict:
        """
        تنفيذ عملية التدقيق.
        """
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""

        logger.info("Procedural Auditor: Starting audit process.")

        try:
            # 1. Extract Graph Structure using LLM
            extraction_response = await ai_client.send_message(
                system_prompt=ProceduralAuditorNode.SYSTEM_PROMPT,
                user_message=f"Analyze this context and extract the fraud detection graph:\n\n{last_message}",
            )

            # Clean JSON
            json_str = extraction_response.replace("```json", "").replace("```", "").strip()
            # Find first { and last }
            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = json_str[start:end]

            graph_data = json.loads(json_str)

            # 2. Build Graph
            graph = GraphBuilder.from_structure(graph_data)

            # 3. Initialize Auditor & Register Rules
            auditor = GraphAuditor(graph)
            auditor.register_rule(ConflictOfInterestRule())
            auditor.register_rule(SuspiciousLocationRule())
            auditor.register_rule(CycleDetectionRule())

            # 4. Run Audit
            audit_results = auditor.run_audit()

            # 5. Compile Report
            # Calculate score (Mock logic: 100 - 20 per fail)
            fails = len([r for r in audit_results if r.status == AuditStatus.FAIL])
            warnings = len([r for r in audit_results if r.status == AuditStatus.WARNING])
            risk_score = (fails * 20.0) + (warnings * 5.0)
            overall_status = (
                AuditStatus.FAIL
                if fails > 0
                else (AuditStatus.WARNING if warnings > 0 else AuditStatus.PASS)
            )

            report = ComplianceReport(
                audit_id=str(uuid.uuid4()),
                target_entity="Context Analysis",
                overall_status=overall_status,
                risk_score=min(risk_score, 100.0),
                findings=audit_results,
                recommendations=[
                    "Verify entity documents" if fails > 0 else "No immediate action required"
                ],
                timestamp=datetime.now().timestamp(),
            )

            # MAF-1.0 Integration: Map to Verification
            maf_verification = {
                "passed": report.overall_status != AuditStatus.FAIL,
                "status": report.overall_status.value.upper(),
                "evidence_ids": [e for r in report.findings for e in r.evidence],
                "gaps": [r.message for r in report.findings if r.status == AuditStatus.FAIL],
                "risk_score": report.risk_score
            }

            # Format Output for Chat
            output_text = "**Procedural Audit Report**\n\n"
            output_text += f"**Status:** {overall_status.value.upper()}\n"
            output_text += f"**Risk Score:** {risk_score}/100\n\n"

            if not audit_results:
                output_text += "ℹ️ No relevant entities found for audit.\n"
            elif fails == 0 and warnings == 0:
                output_text += "✅ No procedural violations detected.\n"
            else:
                for res in audit_results:
                    if res.status != AuditStatus.PASS:
                        icon = "❌" if res.status == AuditStatus.FAIL else "⚠️"
                        output_text += f"{icon} **{res.rule_id}**: {res.message}\n"
                        if res.evidence:
                            output_text += f"   *Evidence:* {', '.join(res.evidence)}\n"

            # Return update to state
            return {
                "messages": [AIMessage(content=output_text, name="procedural_auditor")],
                "user_context": {"last_audit_report": report.model_dump()},
                "maf_verification": maf_verification,  # Push to state for Kernel
                "review_score": None,  # Reset review
                "review_feedback": None,
            }

        except Exception as e:
            logger.error(f"Audit failed: {e}", exc_info=True)
            return {
                "messages": [
                    AIMessage(content=f"⚠️ Audit Process Failed: {e}", name="procedural_auditor")
                ]
            }


async def procedural_auditor_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    غلاف (Wrapper) لعقدة المدقق ليتم استدعاؤها داخل LangGraph.
    """
    return await ProceduralAuditorNode.run_audit(state, ai_client)
