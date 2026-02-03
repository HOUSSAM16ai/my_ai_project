import sys
import unittest
from typing import Any, NotRequired, TypedDict
from unittest.mock import MagicMock


# 1. Mock AgentState to avoid importing app.services.chat
class AgentState(TypedDict):
    messages: list[Any]
    next: str
    plan: list[str]
    current_step_index: int
    search_results: list[Any]
    user_context: dict
    final_response: str
    review_packet: NotRequired[dict]
    maf_proposal: NotRequired[dict]
    maf_attack: NotRequired[dict]
    maf_verification: NotRequired[dict]
    iteration_count: NotRequired[int]
    supervisor_instruction: NotRequired[str]
    audit_bundle: NotRequired[dict]

# 2. Patch sys.modules BEFORE importing kernel
mock_state_module = MagicMock()
mock_state_module.AgentState = AgentState
sys.modules["app.services.chat.graph.state"] = mock_state_module

# Now we can import kernel
from app.core.maf.kernel import MAFKernel
from app.core.maf.spec import MAFPhase, ReviewChecklist, ReviewPacket


class TestCritiqueLoop(unittest.TestCase):
    def test_critique_loop_rejection(self):
        """
        Verifies that a Rejected review triggers the Maker-Checker loop (back to Writer).
        """
        # 1. Setup State: Just finished Review (Attack Phase), result is REJECT
        packet = ReviewPacket(
            checklist=ReviewChecklist(
                requirements_met=False,
                constraints_met=False,
                assumptions_flagged=["Assumed infinite resources"],
                contradictions_found=[],
                justification_clear=False,
                worst_case_analysis="System Crash",
                minimal_fix_suggestion="Add resource limits",
            ),
            score=5.0,
            actionable_feedback="Please fix the resource assumption.",
            recommendation="REJECT"
        )

        state: AgentState = {
            "messages": [],
            "next": "reviewer",
            "plan": ["step1"],
            "current_step_index": 1,
            "search_results": [],
            "user_context": {},
            "final_response": "Bad Response",
            "review_packet": packet.model_dump(),
            # Legacy fields for determining phase
            "maf_proposal": {"claims": [], "raw_content": "Bad Response"},
            # maf_attack is usually set by reviewer too
            "maf_attack": {"successful": True, "severity": 5.0},
            "iteration_count": 0
        }

        # 2. Kernel Decision
        phase = MAFKernel.determine_phase(state)
        # Expect VERIFY because attack/review is done
        self.assertEqual(phase, MAFPhase.VERIFY)

        decision = MAFKernel.decide_next_node(state)

        # 3. Assertions
        print(f"Decision 1 (Reject): {decision}")
        self.assertEqual(decision["next"], "writer")
        self.assertTrue(decision.get("increment_iteration"))
        self.assertIn("CRITICAL FEEDBACK", decision["instruction"])
        self.assertIn("Add resource limits", decision["instruction"])

    def test_critique_loop_approval(self):
        """
        Verifies that an Approved review proceeds to Verification/Sealing.
        """
        # 1. Setup State: Just finished Review, result is APPROVE
        packet = ReviewPacket(
            checklist=ReviewChecklist(
                requirements_met=True,
                constraints_met=True,
                assumptions_flagged=[],
                contradictions_found=[],
                justification_clear=True,
                worst_case_analysis="None",
                minimal_fix_suggestion="None",
            ),
            score=9.5,
            actionable_feedback="Good job.",
            recommendation="APPROVE"
        )

        state: AgentState = {
            "messages": [],
            "next": "reviewer",
            "plan": ["step1"],
            "current_step_index": 2,
            "search_results": [],
            "user_context": {},
            "final_response": "Good Response",
            "review_packet": packet.model_dump(),
            "maf_proposal": {"claims": [], "raw_content": "Good Response"},
            "maf_attack": {"successful": False, "severity": 0.0},
            "iteration_count": 1
        }

        # 2. Kernel Decision
        decision = MAFKernel.decide_next_node(state)

        # 3. Assertions
        print(f"Decision 2 (Approve): {decision}")
        # Should proceed to procedural_auditor (Verify Phase)
        self.assertEqual(decision["next"], "procedural_auditor")

if __name__ == "__main__":
    unittest.main()
