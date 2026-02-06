"""
DSPy Modules for Overmind Cognitive Functions.
----------------------------------------------
This module contains DSPy Signatures and Modules used for:
1. Objective Refinement
2. Context Enrichment
3. Reasoning Optimization

Standards:
- Use dspy.Signature and dspy.Module
- Output structured data where possible
"""

import json

import dspy


class RefineObjectiveSignature(dspy.Signature):
    """
    Refine a raw mission objective into a structured, actionable plan.
    Extract critical metadata (Subject, Year, Branch, Exam Reference) if applicable.
    The refined objective should be clear, concise, and ready for an autonomous agent.
    """

    objective: str = dspy.InputField(desc="The raw user objective or query.")

    refined_objective: str = dspy.OutputField(
        desc="A refined, technical, and actionable version of the objective."
    )
    metadata_json: str = dspy.OutputField(
        desc="A JSON string containing extracted metadata (e.g., {'year': '2024', 'subject': 'Math'}). Return '{}' if none."
    )
    reasoning: str = dspy.OutputField(desc="Brief reasoning behind the refinement.")


class ObjectiveRefinerModule(dspy.Module):
    """
    DSPy Module to refine objectives using Chain of Thought.
    """

    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(RefineObjectiveSignature)

    def forward(self, objective: str):
        """
        Refine the objective.
        """
        # Ensure we return a prediction object compatible with dspy
        return self.prog(objective=objective)


def parse_metadata(json_str: str) -> dict[str, object]:
    """Helper to safely parse the JSON output."""
    try:
        # Clean potential markdown code blocks
        clean_str = json_str.strip()
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        return json.loads(clean_str.strip())
    except Exception:
        return {}
