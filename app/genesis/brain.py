"""
Genesis Cortex: The Abstracted Brain.
Simplifies interaction with the AI Provider.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from app.core.ai_client_factory import get_ai_client

logger = logging.getLogger("genesis.brain")

class Cortex:
    """
    The Thinking Unit.
    Wraps the AI Client to provide a simple 'think' interface.
    """

    def __init__(self, model: str = "gpt-4o"):
        self.client = get_ai_client()
        self.model = model

    def think(self, messages: List[dict], tools: Optional[List[dict]] = None) -> Any:
        """
        Send context to the LLM and get a response (Message object).
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0, # Deterministic for agents
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            # Check if client is "Mock" or Real to handle properly
            # The protocol wrapper in ai_client_factory uses chat.completions.create
            response = self.client.chat.completions.create(**kwargs)

            choice = response.choices[0]
            return choice.message

        except Exception as e:
            logger.error(f"Cortex Failure: {e}")
            raise RuntimeError(f"Brain freeze: {e}")
