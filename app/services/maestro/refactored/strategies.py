"""
LLM execution strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LLMStrategy(ABC):
    """Base LLM execution strategy."""

    @abstractmethod
    async def can_execute(self) -> bool:
        """Check if strategy can execute."""
        pass

    @abstractmethod
    async def execute(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str | None,
    ) -> str:
        """Execute strategy."""
        pass


class BaseServiceStrategy(LLMStrategy):
    """Strategy using base service text_completion."""

    def __init__(self, base_service: Any):
        self._base = base_service

    async def can_execute(self) -> bool:
        """Check if base service is available."""
        return self._base is not None and hasattr(self._base, "text_completion")

    async def execute(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str | None,
    ) -> str:
        """Execute via base service."""
        result = self._base.text_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=0,
            fail_hard=False,
            model=model,
        )

        if not result or not result.strip():
            raise ValueError("Empty response from base service")

        return result


class ForgeCodeStrategy(LLMStrategy):
    """Strategy using forge_new_code method."""

    def __init__(self, base_service: Any):
        self._base = base_service

    async def can_execute(self) -> bool:
        """Check if forge_new_code is available."""
        return self._base is not None and hasattr(self._base, "forge_new_code")

    async def execute(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str | None,
    ) -> str:
        """Execute via forge_new_code."""
        merged = f"{system_prompt.strip()}\n\nUSER:\n{user_prompt}"
        resp = self._base.forge_new_code(merged, model=model)

        if isinstance(resp, dict) and resp.get("status") == "success":
            answer = (resp.get("answer") or "").strip()
            if not answer:
                raise ValueError("Empty answer from forge_new_code")
            return answer

        error = resp.get("error") if isinstance(resp, dict) else "forge_failure"
        raise RuntimeError(f"forge_new_code failed: {error}")


class DirectLLMStrategy(LLMStrategy):
    """Strategy using direct LLM client."""

    async def can_execute(self) -> bool:
        """Check if LLM client is available."""
        try:
            from app.services.llm_client import get_llm_client
            return get_llm_client() is not None
        except ImportError:
            return False

    async def execute(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str | None,
    ) -> str:
        """Execute via direct LLM client."""
        from app.services.llm_client import get_llm_client

        client = get_llm_client()
        completion = client.chat.completions.create(
            model=model or "gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = completion.choices[0].message.content or ""
        if not content or not content.strip():
            raise ValueError("Empty content from LLM client")

        return content.strip()
