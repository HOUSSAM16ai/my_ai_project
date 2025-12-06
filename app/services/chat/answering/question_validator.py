# app/services/chat/answering/question_validator.py
"""Question validator with CC ≤ 3."""


class QuestionValidator:
    """Validates questions. CC ≤ 3"""

    def validate(self, question: str) -> tuple[bool, str]:
        """Validate question. CC=3"""
        if not question or not question.strip():
            return False, "Question is empty"

        if len(question) > 5000:
            return False, "Question too long"

        if len(question) < 3:
            return False, "Question too short"

        return True, ""
