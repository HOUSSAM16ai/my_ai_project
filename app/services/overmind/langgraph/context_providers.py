from __future__ import annotations

import os
from dataclasses import dataclass

import dspy

from app.core.logging import get_logger
from app.services.overmind.domain.dspy_modules import ObjectiveRefinerModule, parse_metadata
from app.services.overmind.langgraph.context_contracts import RefineResult, Snippet
from app.services.overmind.langgraph.research_agent_client import ResearchAgentClient

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class NoopObjectiveRefiner:
    """
    منقح هدف افتراضي يعيد الهدف كما هو.
    """

    async def refine(self, objective: str) -> RefineResult:
        """
        يعيد الهدف كما ورد دون تعديل.
        """
        return RefineResult(refined_objective=objective, metadata={})


@dataclass(frozen=True, slots=True)
class NullSnippetRetriever:
    """
    مسترجع مقتطفات فارغ يستخدم عند غياب التكاملات الخارجية.
    """

    async def retrieve(
        self,
        query: str,
        *,
        context: dict[str, object],
        metadata: dict[str, object],
        max_snippets: int,
    ) -> list[Snippet]:
        """
        يعيد قائمة فارغة لتجنب آثار جانبية غير لازمة.
        """
        return []


@dataclass(frozen=True, slots=True)
class ResearchAgentSnippetRetriever:
    """
    مسترجع مقتطفات عبر خدمة Research Agent الخارجية.
    """

    client: ResearchAgentClient

    async def retrieve(
        self,
        query: str,
        *,
        context: dict[str, object],
        metadata: dict[str, object],
        max_snippets: int,
    ) -> list[Snippet]:
        """
        يستدعي خدمة Research Agent ويحوّل النتائج إلى مقتطفات موحّدة.
        """
        filters = _extract_metadata_filters(context, metadata)
        return await self.client.search(query=query, filters=filters, limit=max_snippets)


@dataclass(frozen=True, slots=True)
class ResearchAgentObjectiveRefiner:
    """
    منقح هدف يعتمد على خدمة Research Agent.
    """

    client: ResearchAgentClient
    api_key: str

    async def refine(self, objective: str) -> RefineResult:
        """
        يرسل الهدف إلى خدمة Research Agent لإعادة صياغته.
        """
        result = await self.client.refine(query=objective, api_key=self.api_key)
        return RefineResult(
            refined_objective=result.refined_query,
            metadata=result.metadata,
        )


@dataclass(frozen=True, slots=True)
class DSPyObjectiveRefiner:
    """
    منقح هدف يعتمد على DSPy (Local/LLM).
    """

    module: ObjectiveRefinerModule

    async def refine(self, objective: str) -> RefineResult:
        """
        يستخدم DSPy لتنقيح الهدف.
        """
        try:
            lm = None
            # Check if dspy is configured. If not, create a local LM instance.
            if not dspy.settings.lm:
                api_key = os.environ.get("OPENAI_API_KEY")
                base_url = os.environ.get("OPENAI_BASE_URL")
                model = os.environ.get("OPENAI_MODEL", "gpt-4o")
                if api_key:
                    lm = dspy.LM(model=model, api_key=api_key, base_url=base_url)
                else:
                    logger.warning("DSPy not configured and no OPENAI_API_KEY found.")
                    return RefineResult(refined_objective=objective, metadata={})

            # Use thread-local context if we created a local LM, otherwise use global default
            if lm:
                with dspy.context(lm=lm):
                    prediction = self.module(objective=objective)
            else:
                prediction = self.module(objective=objective)

            metadata = parse_metadata(prediction.metadata_json)

            logger.info(f"DSPy Refined: {prediction.refined_objective}")

            return RefineResult(
                refined_objective=prediction.refined_objective,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"DSPy refinement failed: {e}")
            return RefineResult(refined_objective=objective, metadata={})


def build_default_retriever() -> NullSnippetRetriever | ResearchAgentSnippetRetriever:
    """
    بناء المسترجع الافتراضي وفق متغيرات البيئة.
    """
    base_url = os.environ.get("RESEARCH_AGENT_URL")
    if not base_url:
        logger.info("Research Agent URL غير متوفر، سيتم تعطيل الاسترجاع الخارجي.")
        return NullSnippetRetriever()
    return ResearchAgentSnippetRetriever(
        client=ResearchAgentClient(base_url=base_url),
    )


def build_default_refiner() -> object:
    """
    بناء المنقح الافتراضي.
    يفضل DSPy إذا كان متاحاً، ثم Research Agent.
    """
    # 1. Try DSPy (Primary for Super Mission)
    if os.environ.get("OPENAI_API_KEY") or dspy.settings.lm:
        return DSPyObjectiveRefiner(module=ObjectiveRefinerModule())

    # 2. Fallback to Research Agent
    base_url = os.environ.get("RESEARCH_AGENT_URL")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if base_url and api_key:
        return ResearchAgentObjectiveRefiner(
            client=ResearchAgentClient(base_url=base_url),
            api_key=api_key,
        )

    # 3. Fallback to No-op
    logger.info("No refinement backend available (DSPy or Research Agent).")
    return NoopObjectiveRefiner()


def _extract_metadata_filters(
    context: dict[str, object], metadata: dict[str, object]
) -> dict[str, object]:
    """
    استخراج مرشحات البحث من السياق المشترك إن وجدت.
    """
    candidate = context.get("metadata_filters")
    if isinstance(candidate, dict):
        return candidate
    return metadata
