"""
LLM Adapter - Infrastructure Layer
==================================
Adapter for LLM client interactions.
"""
from __future__ import annotations

import json
import math
import os
import time
from typing import Any

from ..domain.models import CompletionRequest, StructuredJsonRequest


class LLMAdapter:
    """Adapter for LLM client operations."""

    def __init__(self, get_llm_client_func):
        """
        Initialize adapter with LLM client getter.

        Args:
            get_llm_client_func: Function to get LLM client instance
        """
        self.get_llm_client = get_llm_client_func

    def text_completion(self, request: CompletionRequest) -> str:
        """
        Generate text completion using LLM.

        Implements retry logic with exponential backoff.
        """

        model_name = request.model or self._select_default_model()
        backoff_base = 0.25
        last_err: Any = None

        for attempt in range(request.max_retries + 1):
            try:
                client = self.get_llm_client()
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": request.user_prompt},
                    ],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                content = resp.choices[0].message.content or ""
                return content.strip()

            except Exception as e:
                last_err = e
                error_msg = str(e).lower()

                if "500" in error_msg or "server" in error_msg:
                    self._log(
                        f"[text_completion] Server error (500) on attempt {attempt + 1}: {e}",
                        level="error",
                    )
                elif "timeout" in error_msg:
                    self._log(
                        f"[text_completion] Timeout on attempt {attempt + 1}: {e}",
                        level="warning",
                    )
                else:
                    self._log(
                        f"[text_completion] attempt={attempt + 1} failed: {e}",
                        level="warning",
                    )

                if attempt < request.max_retries:
                    time.sleep(backoff_base * math.pow(1.45, attempt))

        if last_err:
            raise last_err
        if request.fail_hard:
            raise RuntimeError("text_completion_failed:unknown_error")
        return ""

    def structured_json(self, request: StructuredJsonRequest) -> dict[str, Any] | None:
        """
        Generate structured JSON response.

        Implements JSON extraction and validation.
        """
        from app.utils.text_processing import (
            extract_first_json_object,
            strip_markdown_fences,
        )

        required = []
        if isinstance(request.format_schema, dict):
            req = request.format_schema.get("required")
            if isinstance(req, list):
                required = req

        sys_prompt = (
            request.system_prompt.strip()
            + "\nYou MUST output ONLY one valid JSON object. No markdown fences. No commentary."
        )

        last_err: Any = None

        for attempt in range(request.max_retries + 1):
            completion_req = CompletionRequest(
                system_prompt=sys_prompt,
                user_prompt=request.user_prompt,
                temperature=request.temperature,
                max_tokens=900,
                max_retries=0,
                fail_hard=False,
                model=request.model,
            )

            raw = self.text_completion(completion_req)

            if not raw:
                last_err = "empty_response"
            else:
                candidate = extract_first_json_object(raw)
                if not candidate:
                    candidate = self._soft_recover_json(raw, strip_markdown_fences)
                if not candidate:
                    last_err = "no_json_found"
                else:
                    obj, err = self._safe_json_load(candidate)
                    if err:
                        last_err = f"json_parse_error:{err}"
                    elif not isinstance(obj, dict):
                        last_err = "parsed_not_dict"
                    else:
                        missing = [k for k in required if k not in obj]
                        if missing:
                            last_err = f"missing_required:{missing}"
                        else:
                            return obj

            self._log(
                f"[structured_json] attempt={attempt + 1} failed: {last_err}",
                level="warning",
            )

            if attempt < request.max_retries:
                time.sleep(0.28 * (attempt + 1))

        if request.fail_hard:
            raise RuntimeError(f"structured_json_failed:{last_err}")
        return None

    def _select_default_model(self) -> str:
        """Select default model from configuration."""
        from app.config.ai_models import get_ai_config

        ai_config = get_ai_config()

        # Check for overrides
        force_model = os.getenv("MAESTRO_FORCE_MODEL")
        if force_model:
            return force_model

        override_model = os.getenv("AI_MODEL_OVERRIDE")
        if override_model:
            return override_model

        return ai_config.primary_model

    def _soft_recover_json(self, raw: str, strip_fences_func) -> str | None:
        """Attempt to recover JSON from malformed response."""
        if os.getenv("MAESTRO_JSON_SOFT_RECOVER", "1") != "1":
            return None

        text = strip_fences_func(raw)
        starts = [i for i, c in enumerate(text) if c == "{"]

        for st in starts:
            depth = 0
            for j, ch in enumerate(text[st:], start=st):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[st : j + 1]
                        try:
                            json.loads(candidate)
                            return candidate
                        except Exception:
                            continue
        return None

    def _safe_json_load(self, payload: str) -> tuple[Any | None, str | None]:
        """Safely load JSON with error handling."""
        try:
            return json.loads(payload), None
        except Exception as e:
            return None, str(e)

    def _log(self, msg: str, level: str = "info") -> None:
        """Simple logging."""
        import logging
        logger = logging.getLogger("maestro.llm_adapter")
        getattr(logger, level, logger.info)(msg)


__all__ = ["LLMAdapter"]
