"""
Model Selector - Infrastructure Layer
=====================================
Selects appropriate AI model based on context.
"""
from __future__ import annotations

import os
from typing import Any


class ModelSelector:
    """Selects appropriate model for generation tasks."""

    def select_model(self, explicit: str | None = None, task: Any = None) -> str:
        """
        Select model based on explicit request, task context, or defaults.

        Priority:
        1. Explicit model parameter
        2. MAESTRO_FORCE_MODEL env var
        3. AI_MODEL_OVERRIDE env var
        4. Task-specific model (if task provided)
        5. Central config primary model

        Args:
            explicit: Explicitly requested model
            task: Task object for context-based selection

        Returns:
            Selected model name
        """
        # 1. Explicit parameter
        if explicit:
            return explicit

        # 2. Force model override
        force_model = os.getenv("MAESTRO_FORCE_MODEL")
        if force_model:
            return force_model

        # 3. General override
        override_model = os.getenv("AI_MODEL_OVERRIDE")
        if override_model:
            return override_model

        # 4. Task-specific model
        if task and hasattr(task, "model") and task.model:
            return task.model

        # 5. Central config
        from app.config.ai_models import get_ai_config

        ai_config = get_ai_config()
        return ai_config.primary_model


__all__ = ["ModelSelector"]
