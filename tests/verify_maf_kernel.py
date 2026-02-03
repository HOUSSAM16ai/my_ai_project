import unittest

from app.core.maf.kernel import MAFKernel
from app.core.maf.spec import MAFPhase


class TestMAFKernel(unittest.TestCase):
    def test_determine_phase_generate(self):
        state = {}
        phase = MAFKernel.determine_phase(state)
        self.assertEqual(phase, MAFPhase.GENERATE)

    def test_determine_phase_attack(self):
        # Proposal must be present (truthy or just present? logic says 'if not proposal')
        # We need to make sure proposal is treated as present.
        state = {"maf_proposal": {"claims": [], "raw_content": "plan"}}
        phase = MAFKernel.determine_phase(state)
        self.assertEqual(phase, MAFPhase.ATTACK)

    def test_determine_phase_verify(self):
        state = {
            "maf_proposal": {"claims": [], "raw_content": "plan"},
            "maf_attack": {"successful": False, "severity": 0.0, "feedback": "Good"}
        }
        phase = MAFKernel.determine_phase(state)
        self.assertEqual(phase, MAFPhase.VERIFY)

    def test_determine_phase_seal(self):
        state = {
            "maf_proposal": {"claims": [], "raw_content": "plan"},
            "maf_attack": {"successful": False, "feedback": "Good"},
            "maf_verification": {"passed": True}
        }
        phase = MAFKernel.determine_phase(state)
        self.assertEqual(phase, MAFPhase.SEAL)

    def test_decide_next_node_flow(self):
        # 1. Generate (No plan -> Planner)
        state = {}
        decision = MAFKernel.decide_next_node(state)
        self.assertEqual(decision["next"], "planner")

        # 1b. Generate (Plan exists -> SuperReasoner)
        state = {"plan": ["step1"]}
        decision = MAFKernel.decide_next_node(state)
        self.assertEqual(decision["next"], "super_reasoner")

        # 2. Attack
        state = {"maf_proposal": {"claims": [], "raw_content": "prop"}}
        decision = MAFKernel.decide_next_node(state)
        self.assertEqual(decision["next"], "reviewer")
        self.assertTrue("ATTACK PHASE" in decision["instruction"])

        # 3. Verify
        state = {
            "maf_proposal": {"claims": [], "raw_content": "prop"},
            "maf_attack": {"successful": False, "feedback": "Good", "severity": 0.0}
        }
        decision = MAFKernel.decide_next_node(state)
        self.assertEqual(decision["next"], "procedural_auditor")

        # 4. Seal (Pass)
        state = {
            "maf_proposal": {"claims": [], "raw_content": "prop"},
            "maf_attack": {"successful": False, "feedback": "Good", "severity": 0.0},
            "maf_verification": {"passed": True, "status": "PASS"}
        }
        decision = MAFKernel.decide_next_node(state)
        self.assertEqual(decision["next"], "writer")
        self.assertTrue("SEAL PHASE" in decision["instruction"])

        # 5. Fail Loop (Verification Failed)
        state = {
            "maf_proposal": {"claims": [], "raw_content": "prop"},
            "maf_attack": {"successful": False, "feedback": "Good", "severity": 0.0},
            "maf_verification": {"passed": False, "status": "FAIL", "gaps": ["Error"]},
            "iteration_count": 0
        }
        decision = MAFKernel.decide_next_node(state)
        self.assertEqual(decision["next"], "planner")
        self.assertTrue(decision.get("increment_iteration"))

if __name__ == '__main__':
    unittest.main()
