# app/services/chat/answering/answer_orchestrator.py
"""Answer orchestrator with CC ≤ 5."""

from typing import Any

from .context_retriever import ContextRetriever
from .error_handler import Answer, ErrorHandler
from .llm_invoker import LLMInvoker
from .question_validator import QuestionValidator
from .response_validator import ResponseValidator


class AnswerOrchestrator:
    """
    Orchestrates question answering. CC=5

    Replaces the monolithic answer_question function (CC=41).
    """

    def __init__(self):
        self.question_validator = QuestionValidator()
        self.context_retriever = ContextRetriever()
        self.llm_invoker = LLMInvoker()
        self.response_validator = ResponseValidator()
        self.error_handler = ErrorHandler()

    def answer(self, question: str, user: Any | None = None, context: dict | None = None) -> Answer:
        """
        Answer question. CC=5

        This replaces the original answer_question function which had CC=41.
        """
        context = context or {}

        # Step 1: Validate question
        is_valid, error_msg = self.question_validator.validate(question)
        if not is_valid:
            return Answer(status="error", content=error_msg, error_type="validation")

        # Step 2: Retrieve context
        context_data = self.context_retriever.retrieve(question, context)

        # Step 3: Invoke LLM
        try:
            response = self.llm_invoker.invoke(question, context_data)

            # Step 4: Validate response
            content = self.response_validator.validate(response)

            # Step 5: Return result
            return Answer(
                status="success",
                content=content,
                tokens_used=response.get("tokens", 0),
                model_used=response.get("model", "unknown"),
            )

        except Exception as e:
            return self.error_handler.handle(e)
