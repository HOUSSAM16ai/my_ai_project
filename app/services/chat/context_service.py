from __future__ import annotations

import logging
import time

from app.overmind.planning.deep_indexer_v2 import build_index, summarize_for_prompt

logger = logging.getLogger(__name__)


class CodebaseContextService:
    """
    Service responsible for maintaining a 'Cognitive Map' of the codebase.
    It performs indexing and summarization to provide context to the AI.
    """

    _instance: CodebaseContextService | None = None
    _cached_summary: str | None = None
    _last_index_time: float = 0
    _CACHE_TTL = 3600  # 1 hour cache for the deep index

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> CodebaseContextService:
        if cls._instance is None:
            cls._instance = CodebaseContextService()
        return cls._instance

    def _refresh_index(self) -> str:
        """
        Refreshes the codebase index and generates a new summary.
        This is a blocking operation, should be improved with async or background tasks in future.
        """
        logger.info("Overmind: Refreshing codebase index...")
        try:
            # We limit the scope to ensure speed for the context injection
            index = build_index(root=".", internal_prefixes=("app",))
            summary = summarize_for_prompt(index, max_len=4000)
            self._cached_summary = summary
            self._last_index_time = time.time()
            return summary
        except Exception as e:
            logger.error(f"Overmind: Failed to index codebase: {e}")
            return "ERROR: Could not generate codebase summary."

    def get_context_system_prompt(self) -> str:
        """
        Returns the System Prompt enriched with the Codebase Summary.
        """
        # Lazy load or refresh if TTL expired
        if self._cached_summary is None or (time.time() - self._last_index_time > self._CACHE_TTL):
            self._refresh_index()

        base_prompt = (
            "أنت **Overmind CLI Mindgate**، العقل المدبر للنظام.\n"
            "مهمتك: مساعدة المطورين باستخدام ذكاء خارق وفهم عميق للكود.\n"
            "لديك قدرات تحليلية متقدمة وتعرف تفاصيل المشروع بدقة.\n\n"
            "**معلومات المشروع الحالية (Cognitive Map):**\n"
            f"```\n{self._cached_summary}\n```\n\n"
            "استخدم هذه المعلومات للإجابة بدقة على الأسئلة حول الملفات، الدوال، والهيكلية.\n"
            "لا تهلوس بمسارات غير موجودة. إذا سُئلت عن عدد الأسطر أو الملفات، استخدم الأرقام أعلاه.\n"
            "تحدث بأسلوب تقني محترف، دقيق، وواثق (Overmind Persona)."
        )
        return base_prompt

    def force_refresh(self):
        """Forces a refresh of the index."""
        self._refresh_index()


def get_context_service() -> CodebaseContextService:
    return CodebaseContextService.get_instance()
