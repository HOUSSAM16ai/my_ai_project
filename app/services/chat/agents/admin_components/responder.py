"""
Formal Responder (SRP).
-----------------------
Handles the generation of formal Arabic responses.
"""

from collections.abc import AsyncGenerator

from app.core.interfaces.llm import LLMClient
from app.services.chat.agents.base import FORMAL_ARABIC_STYLE_PROMPT


class FormalResponder:
    """
    Responsible for formatting responses in the required formal Arabic style.
    """

    def __init__(self, ai_client: LLMClient):
        self.ai_client = ai_client

    async def generate(self, question: str) -> AsyncGenerator[str, None]:
        """Generates a formal answer using the LLM."""
        messages = [
            {
                "role": "system",
                "content": f"أنت مساعد إداري خبير.\n{FORMAL_ARABIC_STYLE_PROMPT}",
            },
            {"role": "user", "content": question},
        ]

        async for chunk in self.ai_client.stream_chat(messages):
            content = ""
            if hasattr(chunk, "choices"):  # Legacy object access
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            elif isinstance(chunk, dict):  # Dict access
                choices = chunk.get("choices", [{}])
                if choices:
                    content = choices[0].get("delta", {}).get("content", "")

            if content:
                yield content
