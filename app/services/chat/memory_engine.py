"""
محرك الذاكرة العرضية (Episodic Memory Engine).
----------------------------------------------
يدير هذا المحرك ذاكرة طويلة الأمد للوكلاء، حيث يقوم بتخزين "التجارب" (Experiences)
واسترجاعها لتحسين القرارات المستقبلية.

المبدأ:
1. التذكر (Recall): استرجاع دروس سابقة مشابهة للسياق الحالي.
2. التعلم (Learn): تحليل التفاعل بعد انتهائه (Reflection) وتخزين الدرس المستفاد.
"""

import asyncio
import os
from typing import Optional

from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.retrievers import VectorIndexRetriever

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger

logger = get_logger("memory-engine")

MEMORY_DIR = os.getenv("MEMORY_STORE_DIR", "./data/memory_store")


class EpisodicMemoryEngine:
    """
    محرك الذاكرة العرضية.
    يستخدم VectorStore لتخزين واسترجاع الدروس المستفادة.
    """

    def __init__(self, storage_dir: str = MEMORY_DIR):
        self.storage_dir = storage_dir
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> VectorStoreIndex:
        """تحميل الفهرس من القرص أو إنشاؤه إذا لم يكن موجوداً."""
        if not os.path.exists(self.storage_dir):
            try:
                os.makedirs(self.storage_dir, exist_ok=True)
                # تهيئة فهرس فارغ
                index = VectorStoreIndex.from_documents([])
                index.storage_context.persist(persist_dir=self.storage_dir)
                return index
            except Exception as e:
                logger.error(f"Failed to create memory directory: {e}")
                # Fallback in-memory for read-only systems
                return VectorStoreIndex.from_documents([])

        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
            return load_index_from_storage(storage_context)
        except Exception as e:
            logger.error(f"Failed to load memory index: {e}. Recreating.")
            return VectorStoreIndex.from_documents([])

    async def recall(self, query: str, top_k: int = 3) -> str:
        """
        استرجاع تجارب سابقة مشابهة.
        يعيد نصاً منسقاً يمكن حقنه في سياق النموذج.
        """
        if not query or not self.index:
            return ""

        try:
            # استخدام المسترجع (Retriever)
            retriever: VectorIndexRetriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = await retriever.aretrieve(query)

            if not nodes:
                return ""

            experiences = []
            for n in nodes:
                score = n.metadata.get("score", 0)
                # تنسيق العرض: [Lesson] (Score: X)
                # نعطي أولوية للتجارب ذات التقييم العالي أو المنخفض جداً (تحذيرات)
                prefix = "✅ TIP" if score >= 8 else "⚠️ WARNING"
                experiences.append(f"- {prefix} (Score: {score}): {n.text}")

            if not experiences:
                return ""

            header = "--- 🧠 PAST MEMORY & LESSONS (From Previous Interactions) ---"
            return f"{header}\n" + "\n".join(experiences) + "\n------------------------------------------------------------"

        except Exception as e:
            logger.error(f"Memory recall failed: {e}")
            return ""

    async def learn(
        self,
        ai_client: AIClient,
        query: str,
        plan: list,
        response: str,
        score: float,
        feedback: str,
    ) -> None:
        """
        التعلم من التجربة الحالية.
        يقوم بتحليل التفاعل باستخدام LLM لاستخراج "الدرس" ثم تخزينه.
        """
        if not self.index:
            return

        # 1. Reflection: استخدام الذكاء الاصطناعي لاستخلاص العبرة
        system_prompt = (
            "You are the 'Meta-Cognitive Module' of an intelligent agent. "
            "Your job is to analyze interaction logs and extract a strategic lesson."
        )

        user_prompt = f"""
Analyze this interaction to improve future performance.

User Query: {query}
Plan Executed: {plan}
Review Score: {score}/10
Review Feedback: {feedback}

Task:
Extract a concise "Strategic Lesson" (in Arabic).
- If the score is Low (< 8), explain clearly WHAT went wrong and WHAT to avoid.
- If the score is High (>= 8), explain the key strategy that led to success.

Output ONLY the lesson text.
"""
        try:
            # نستخدم generate_text لاستخراج الدرس
            reflection_response = await ai_client.generate_text(
                prompt=user_prompt, system_prompt=system_prompt
            )
            lesson = reflection_response.content.strip()
        except Exception as e:
            logger.error(f"Reflection logic failed: {e}")
            # Fallback: Use feedback directly
            lesson = f"Feedback received: {feedback}"

        # 2. Storage: تخزين الدرس في الذاكرة
        # نقوم بتضمين الدرس، ونحتفظ بالسياق الكامل في البيانات الوصفية (Metadata)
        try:
            doc = Document(
                text=lesson,  # The embedding is based on the lesson/reflection
                metadata={
                    "original_query": query,  # To help with keyword matching if needed
                    "score": score,
                    "plan": str(plan),
                    "feedback": feedback,
                    "type": "episodic_reflection",
                },
            )

            self.index.insert(doc)

            # Offload blocking I/O to a thread
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self.index.storage_context.persist(persist_dir=self.storage_dir))

            logger.info(f"Memory learned new lesson. Score: {score}")

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")


# Singleton Instance
_instance: Optional[EpisodicMemoryEngine] = None


def get_memory_engine() -> EpisodicMemoryEngine:
    """Factory method to get the singleton memory engine."""
    global _instance
    if _instance is None:
        _instance = EpisodicMemoryEngine()
    return _instance
