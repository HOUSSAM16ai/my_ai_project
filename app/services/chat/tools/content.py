"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import asyncio
import os

from app.core.logging import get_logger
from app.services.content.service import content_service
from app.services.search_engine import get_retriever
from app.services.search_engine.query_refiner import get_refined_query
from app.services.search_engine.fallback_expander import FallbackQueryExpander
from app.services.search_engine.reranker import get_reranker

logger = get_logger("content-tools")


async def get_curriculum_structure(
    level: str | None = None,
    lang: str = "ar",
) -> dict[str, object]:
    """جلب شجرة المنهج الدراسي بالكامل أو لمستوى محدد."""
    try:
        return await content_service.get_curriculum_structure(level)
    except Exception as e:
        logger.error(f"Failed to fetch curriculum structure: {e}")
        return {}


async def search_content(
    q: str | None = None,
    level: str | None = None,
    subject: str | None = None,
    branch: str | None = None,
    set_name: str | None = None,
    year: int | None = None,
    type: str | None = None,
    lang: str | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    """بحث متقدم عن المحتوى التعليمي مع فلاتر قابلة للتوسع."""
    try:
        refined_q = q
        metadata_filters = {}

        api_key = os.environ.get("OPENROUTER_API_KEY")

        # 1. Try Smart Refinement (DSPy)
        if q and api_key:
            try:
                logger.info(f"🔍 DSPy Active: Refining query '{q}'...")
                # Returns Dict now: {'refined_query': ..., 'year': ..., 'subject': ...}
                dspy_result = await asyncio.to_thread(get_refined_query, q, api_key)

                if isinstance(dspy_result, dict):
                    refined_q = dspy_result.get("refined_query", q)
                    # Extract Metadata
                    if dspy_result.get("year"):
                        metadata_filters["year"] = dspy_result["year"]
                        # Auto-inject into args if not provided
                        if year is None: year = dspy_result["year"]

                    if dspy_result.get("subject"):
                        metadata_filters["subject"] = dspy_result["subject"]
                        if subject is None:
                            subject = dspy_result["subject"]

                    logger.info(f"✅ DSPy Result: '{refined_q}' | Metadata: {metadata_filters}")
                else:
                    refined_q = str(dspy_result)
                    logger.info(f"✅ DSPy Result: '{refined_q}' (String only)")

            except Exception as dspy_error:
                logger.warning(f"⚠️ DSPy refinement failed: {dspy_error}")

        # 2. Build Candidate List
        query_candidates = []
        if refined_q and refined_q != q:
            query_candidates.append(refined_q)

        if q:
            variations = FallbackQueryExpander.generate_variations(q)
            for var in variations:
                if var not in query_candidates:
                    query_candidates.append(var)

        # 3. Execution Strategy (The "Self-Correcting Loop")
        # Attempt 1: Strict Semantic Search (Vector + Metadata Filters)
        # Attempt 2: Relaxed Semantic Search (Vector Only)
        # Attempt 3: Keyword Search (Fallback)

        strategies = [
            {"name": "Strict Semantic", "use_vectors": True, "filters": metadata_filters},
            {"name": "Relaxed Semantic", "use_vectors": True, "filters": {}}, # Clear filters
            {"name": "Keyword Fallback", "use_vectors": False, "filters": {}}
        ]

        primary_q = query_candidates[0] if query_candidates else q
        db_url = os.environ.get("DATABASE_URL")

        for strategy in strategies:
            logger.info(f"🔄 Strategy: {strategy['name']}")

            content_ids = []

            if strategy["use_vectors"] and primary_q and db_url:
                try:
                    logger.info("🔍 LlamaIndex Active: Executing Vector Search...")
                    retriever = get_retriever(db_url)

                    # Fetch more candidates for Reranking
                    # We fetch 3x the limit or at least 20 extra to give the reranker enough candidates
                    retrieval_limit = max(limit * 3, limit + 20)
                    nodes = retriever.search(primary_q, limit=retrieval_limit, filters=strategy["filters"])

                    if nodes:
                        logger.info(f"🔍 Reranker Active: Reranking {len(nodes)} candidates...")
                        reranker = get_reranker()
                        nodes = reranker.rerank(primary_q, nodes, top_n=limit)

                    for node in nodes:
                        metadata = getattr(node, "node", node)
                        meta = getattr(metadata, "metadata", {})
                        if isinstance(meta, dict):
                            cid = meta.get("content_id")
                            if cid: content_ids.append(cid)

                    logger.info(f"✅ LlamaIndex Retrieval: Found {len(content_ids)} IDs.")
                except Exception as e:
                    logger.warning(f"⚠️ LlamaIndex search failed: {e}")

            # If Semantic Search was attempted but returned nothing, and we are in Strict mode,
            # we simply continue to the next strategy (Relaxed).
            if strategy["use_vectors"] and not content_ids:
                logger.info("❌ No vectors found in this strategy. Retrying...")
                continue

            # If we have IDs (or are in Keyword mode), query Postgres
            # Note: In Keyword mode (use_vectors=False), content_ids is empty,
            # so ContentService will use the text query 'q'.

            # Use 'q' only for Keyword Fallback
            query_text = None
            if not strategy["use_vectors"]:
                # For Keyword Fallback, use the most "Cleaned" version to avoid AND-ing stop words.
                # query_candidates order is roughly [Refined, Original, ..., Cleaned]
                # We want the last candidate which represents the best keyword representation.
                if query_candidates:
                    query_text = query_candidates[-1]
                    logger.info(f"🔑 Using Optimized Keyword Query: '{query_text}'")
                else:
                    query_text = q

            # For ContentService, we might want to respect the 'year' param
            # ONLY if it was explicitly passed by the caller OR if we are in Strict mode.
            # If we are in Relaxed mode, we should probably clear 'year' from the args passed to SQL
            # to avoid the "Data Inconsistency" issue where Vector says "Match" but SQL says "Wrong Year".

            effective_year = year
            if strategy["name"] == "Relaxed Semantic":
                effective_year = None # Trust the Vector completely

            batch_results = await content_service.search_content(
                q=query_text,
                level=level,
                subject=subject,
                branch=branch,
                set_name=set_name,
                year=effective_year, # Use relaxed year
                type=type,
                lang=lang,
                content_ids=content_ids if strategy["use_vectors"] else None,
                limit=limit,
            )

            if batch_results:
                logger.info(f"🎉 Success! Found {len(batch_results)} results using {strategy['name']}.")
                return batch_results

        return []

    except Exception as e:
        logger.error(f"Search content failed: {e}")
        return []


async def get_content_raw(content_id: str) -> dict[str, str] | None:
    """جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر."""
    try:
        return await content_service.get_content_raw(content_id)
    except Exception as e:
        logger.error(f"Get content raw failed: {e}")
        return None


async def get_solution_raw(content_id: str) -> dict[str, object] | None:
    """جلب الحل الرسمي (Official Solution) لتمرين."""
    data = await content_service.get_content_raw(content_id)
    if data and "solution" in data:
        return {
            "solution_md": data["solution"],
        }
    return None
