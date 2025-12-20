"""
Base

هذا الملف جزء من مشروع CogniForge.
"""

from abc import ABC, abstractmethod
from typing import Any


class ModelProviderAdapter(ABC):
    """Abstract model provider interface"""

    @abstractmethod
    def call_model(
        self, model: str, prompt: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Call AI model"""
        pass

    @abstractmethod
    def estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate API call cost"""
        pass

    @abstractmethod
    def estimate_latency(self, model: str, tokens: int) -> float:
        """Estimate response latency"""
        pass
