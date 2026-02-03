"""
Multi-Agent Fabric Kernel (MAF-Kernel).
---------------------------------------
The core logic engine that enforces the 'Generate -> Attack -> Verify -> Seal' protocol.
This kernel replaces loose LLM routing with a normative state machine.
"""

import logging
from typing import Any

from app.core.maf.spec import AttackReport, AuditStatus, MAFPhase, Verification

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
        verification = state.get("maf_verification")

        # 1. No Proposal -> GENERATE
        if not proposal:
            return MAFPhase.GENERATE

        # 2. Proposal exists. Check for Attack.
        # If no attack report, or if the last cycle was a regeneration, we need to Attack.
        if not attack:
            return MAFPhase.ATTACK

        # 3. Attack exists. Check if it was successful (meaning the proposal was bad).
        # However, the loop logic handles regeneration. If we are here, we have an attack report.
        # We need to see if we should proceed to verify or regenerate.
        # Ideally, if Attack was successful (flaws found), we should RE-GENERATE.
        # But for the linear flow: Proposal -> Attack -> Verify.
        # If Attack found issues, we might skip verify and go back to Generate?
        # Let's check strictness.
        # MAF Spec: Generate -> Attack -> Verify -> Seal.
        # If Attack fails (too many flaws), we don't Seal. We Regenerate.

        attack_obj = AttackReport(**attack) if isinstance(attack, dict) else attack
        if attack_obj and attack_obj.successful:  # Attack successful means "Flaws Found"
            # In a strict loop, this would trigger regeneration.
            # But here we return ATTACK phase to indicate we just finished attacking?
            # No, determine_phase returns what we SHOULD do or where we ARE.
            # Let's define it as "What is the Next Required Action?"
            pass

        # 4. Attack done. Check Verification.
        if not verification:
            # If attack showed severe failure, maybe we shouldn't even verify?
            # But let's follow the linear path for now, or short-circuit.
            if attack_obj and attack_obj.severity > 8.0:
                # Too bad, go back to start?
                # For now, let's proceed to VERIFY to get a full picture, or loop back.
                # Let's assume we proceed to VERIFY to get compliance check too.
                return MAFPhase.VERIFY
            return MAFPhase.VERIFY

        # 5. Verification done. Ready to Seal (or Fail).
        return MAFPhase.SEAL

    @staticmethod
    def decide_next_node(state: dict[str, Any]) -> dict[str, Any]:
        """
        Decides the next graph node based on the MAF Phase and artifact quality.
        """
        phase = MAFKernel.determine_phase(state)

        # State Extraction
        attack_data = state.get("maf_attack")
        verification_data = state.get("maf_verification")

        # Iteration Control (Prevent infinite loops)
        iteration = state.get("iteration_count", 0)
        max_iterations = 3

        logger.info(f"MAF Kernel: Current Phase = {phase}, Iteration = {iteration}")

        # --- PHASE: GENERATE ---
        if phase == MAFPhase.GENERATE:
            # Initial Request or Regeneration
            if iteration > max_iterations:
                logger.warning("Max iterations reached during generation. Forcing Seal.")
                return {
                    "next": "writer",
                    "instruction": "Max iterations reached. Synthesize best available info.",
                }

            # Default to Planner for high-level plan, or Reasoner if specific.
            # We stick to the existing Supervisor logic for *who* to call, but we enforce the *intent*.
            # For simplicity, if no plan, call Planner. If plan exists but no proposal, call Reasoner/Writer?
            # Let's assume Planner -> Proposal.
            # Or Reasoner -> Proposal.
            # If we have a plan in `state["plan"]`, maybe we need execution.
            # Let's route to PLANNER first if empty.
            if not state.get("plan"):
                return {
                    "next": "planner",
                    "instruction": "Generate a rigorous plan. Treat this as a Proposal with Claims.",
                }

            # If Plan exists, we need execution to generate Claims.
            # Route to SuperReasoner or Researcher.
            return {
                "next": "super_reasoner",
                "instruction": "Execute the plan. Output a Proposal with supported Claims.",
            }

        # --- PHASE: ATTACK ---
        if phase == MAFPhase.ATTACK:
            return {
                "next": "reviewer",
                "instruction": "ATTACK PHASE: Act as an Adversary. Find flaws, counterexamples, and logical gaps. Output an Attack Report.",
            }

        # --- PHASE: VERIFY ---
        if phase == MAFPhase.VERIFY:
            # Check if attack was too severe to even verify?
            if attack_data:
                att = AttackReport(**attack_data)
                if att.successful and att.severity > 9.0:
                    # Critical failure. Skip verification, go to Planner to Fix.
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
                attack = AttackReport(**attack_data) if attack_data else None

                # REJECTION CRITERIA
                verification_failed = not ver.passed or ver.status == AuditStatus.FAIL
                attack_critical = attack and attack.successful and attack.severity > 7.0

                if (verification_failed or attack_critical) and iteration < max_iterations:
                    # LOOP BACK
                    feedback = (
                        f"Verification Failed: {ver.gaps}"
                        if verification_failed
                        else f"Attack Severity {attack.severity}: {attack.feedback}"
                    )
                    return {
                        "next": "planner",  # Or Reasoner
                        "instruction": f"REJECTED. {feedback}. Refine the solution.",
                        "increment_iteration": True,
                    }

            # APPROVAL
            return {
                "next": "writer",
                "instruction": "SEAL PHASE: Format the final output as a Certified Audit Bundle. Include Claims, Evidence, and Audit Log.",
            }

        return {"next": "FINISH", "instruction": "Protocol Complete."}
