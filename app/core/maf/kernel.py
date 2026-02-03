"""
Multi-Agent Fabric Kernel (MAF-Kernel).
---------------------------------------
The core logic engine that enforces the 'Generate -> Attack -> Verify -> Seal' protocol.
This kernel replaces loose LLM routing with a normative state machine.
"""

import logging
from typing import Any

from app.core.maf.spec import AttackReport, MAFPhase, ReviewPacket, Verification

logger = logging.getLogger(__name__)


class MAFKernel:
    """
    The Orchestrator that governs the Agent Fabric.
    """

    @staticmethod
    def determine_phase(state: dict[str, Any]) -> MAFPhase:
        """
        Analyzes the state to determine the current MAF Phase.
        """
        proposal = state.get("maf_proposal")
        attack = state.get("maf_attack")
        review_packet = state.get("review_packet")
        verification = state.get("maf_verification")

        # 1. No Proposal -> GENERATE
        if not proposal and not state.get("final_response"):
             # If neither formal proposal nor raw response exists
            return MAFPhase.GENERATE

        # 2. Proposal exists. Check for Attack/Review.
        # We need a ReviewPacket (Reviewer) OR AttackReport (Legacy/Adversary).
        if not attack and not review_packet:
            return MAFPhase.ATTACK

        # 3. Attack done. Check Verification.
        if not verification:
            return MAFPhase.VERIFY

        # 4. Verification done. Ready to Seal (or Fail).
        return MAFPhase.SEAL

    @staticmethod
    def decide_next_node(state: dict[str, Any]) -> dict[str, Any]:
        """
        Decides the next graph node based on the MAF Phase and artifact quality.
        """
        phase = MAFKernel.determine_phase(state)

        # State Extraction
        attack_data = state.get("maf_attack")
        review_data = state.get("review_packet")
        verification_data = state.get("maf_verification")

        # Iteration Control (Prevent infinite loops)
        iteration = state.get("iteration_count", 0)
        max_iterations = 3

        logger.info(f"MAF Kernel: Current Phase = {phase}, Iteration = {iteration}")

        # --- PHASE: GENERATE ---
        if phase == MAFPhase.GENERATE:
            if iteration > max_iterations:
                return {
                    "next": "writer",
                    "instruction": "Max iterations reached. Synthesize best available info immediately.",
                }

            # If we have a specific "Next Step" plan, follow it?
            # For now, default to Planner -> Writer flow.
            if not state.get("plan"):
                return {
                    "next": "planner",
                    "instruction": "Generate a rigorous plan. Treat this as a Proposal with Claims.",
                }

            # If plan exists, execute.
            return {
                "next": "writer", # Direct to writer for efficiency in chat
                "instruction": "Execute the plan. Output a Proposal with supported Claims.",
            }

        # --- PHASE: ATTACK / CRITIQUE ---
        if phase == MAFPhase.ATTACK:
            return {
                "next": "reviewer",
                "instruction": "ATTACK PHASE: Act as the Strategic Auditor. Perform Maker-Checker analysis.",
            }

        # --- PHASE: VERIFY ---
        if phase == MAFPhase.VERIFY:
            # 1. CHECK MAKER-CHECKER LOOP (ReviewPacket)
            if review_data:
                packet = ReviewPacket(**review_data)

                # If Rejected, Loop Back IMMEDIATELY (Short-Circuit)
                if packet.recommendation == "REJECT":
                    if iteration >= max_iterations:
                         logger.warning("Max iterations reached despite Rejection. Proceeding to Verify.")
                    else:
                        logger.info("Maker-Checker: REJECTED. Looping back to Writer.")
                        return {
                            "next": "writer",
                            "instruction": f"CRITICAL FEEDBACK (Reviewer): {packet.actionable_feedback}. Minimal Fix: {packet.checklist.minimal_fix_suggestion}",
                            "increment_iteration": True
                        }

            # 2. CHECK ADVERSARIAL ATTACK (Legacy/Parallel)
            if attack_data and not review_data:
                att = AttackReport(**attack_data)
                if att.successful and att.severity > 9.0:
                    return {
                        "next": "planner",
                        "instruction": f"Previous proposal destroyed by adversary (Severity {att.severity}). Create a NEW plan to address: {att.feedback}",
                    }

            return {
                "next": "procedural_auditor",
                "instruction": "VERIFY PHASE: Check compliance, evidence existence, and logical consistency. Output Verification.",
            }

        # --- PHASE: SEAL ---
        if phase == MAFPhase.SEAL:
            # Check Verification Status
            if verification_data:
                ver = Verification(**verification_data)

                # REJECTION CRITERIA
                if not ver.passed and iteration < max_iterations:
                    return {
                        "next": "planner",
                        "instruction": f"Verification Failed: {ver.gaps}. Refine the solution.",
                        "increment_iteration": True,
                    }

            # APPROVAL
            return {
                "next": "writer", # Or specialized "Sealer"
                "instruction": "SEAL PHASE: Format the final output as a Certified Audit Bundle.",
            }

        return {"next": "FINISH", "instruction": "Protocol Complete."}
