from langchain_core.tools import tool
from typing import Literal

DiagnosisLevel = Literal["Beginner", "Average", "Advanced"]

@tool("diagnose_student_level")
def diagnose_student_level(last_interaction: str) -> DiagnosisLevel:
    """
    Analyzes the student's last interaction to estimate their proficiency level.
    Useful for tailoring the complexity of the explanation.

    Args:
        last_interaction (str): The last message or query from the student.

    Returns:
        str: One of 'Beginner', 'Average', 'Advanced'.
    """
    # Mock/Stub implementation
    # This logic is a placeholder. Real logic would involve LLM analysis of the conversation depth.

    text = last_interaction.lower()

    if any(word in text for word in ["basic", "simple", "what is", "explain", "help", "i don't understand"]):
        return "Beginner"

    if any(word in text for word in ["optimize", "complex", "proof", "challenge", "hard", "advanced"]):
        return "Advanced"

    return "Average"
