import asyncio
import os

from llama_index.core.schema import NodeWithScore, TextNode

from app.core.logging import get_logger
from app.services.search_engine.fallback_expander import FallbackQueryExpander
from app.services.search_engine.models import SearchRequest, SearchResult
from app.services.search_engine.query_refiner import get_refined_query
from app.services.search_engine.reranker import get_reranker
from app.services.search_engine.strategies import (
    KeywordStrategy,
    RelaxedVectorStrategy,
    SearchStrategy,
    StrictVectorStrategy,
)

logger = get_logger("search-orchestrator")


class SearchOrchestrator:
    """
    Orchestrates the search process:
    1. Query Refinement (DSPy)
    2. Query Expansion (Fallback)
    3. Strategy Execution (Strict -> Relaxed -> Keyword)
    4. Global Reranking (Cross-Encoder)
    """

    def __init__(self):
        self.strategies: list[SearchStrategy] = [
            StrictVectorStrategy(),
            RelaxedVectorStrategy(),
            KeywordStrategy(),
        ]

    async def search(self, request: SearchRequest) -> list[SearchResult]:
        original_q = request.q
        refined_q = original_q

        # 1. DSPy Refinement
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if original_q and api_key:
            try:
                logger.info(f"🔍 DSPy Active: Refining query '{original_q}'...")
                dspy_result = await asyncio.to_thread(get_refined_query, original_q, api_key)

                if isinstance(dspy_result, dict):
                    refined_q = dspy_result.get("refined_query", original_q)
                    # Update filters if found
                    if dspy_result.get("year"):
                        request.filters.year = dspy_result["year"]
                    if dspy_result.get("subject"):
                        request.filters.subject = dspy_result["subject"]
                    if dspy_result.get("branch"):
                        request.filters.branch = dspy_result["branch"]

                    logger.info(
                        f"✅ DSPy Result: '{refined_q}' | Filters: {request.filters.model_dump(exclude_none=True)}"
                    )
                else:
                    logger.warning("⚠️ DSPy returned unexpected format.")

            except Exception as e:
                logger.warning(f"⚠️ DSPy refinement failed: {e}")

        # Update request with refined query for Vector Search
        request.q = refined_q

        # 2. Execute Strategies
        candidates: list[SearchResult] = []

        for strategy in self.strategies:
            logger.info(f"🔄 Strategy: {strategy.name}")

            if isinstance(strategy, KeywordStrategy):
                variations = FallbackQueryExpander.generate_variations(original_q)
                if variations:
                    clean_q = variations[-1]
                    logger.info(f"🔑 Using Optimized Keyword Query: '{clean_q}'")
                    request.q = clean_q
                else:
                    request.q = original_q

            try:
                results = await strategy.execute(request)
                if results:
                    logger.info(f"Strategy {strategy.name} found {len(results)} candidates.")
                    candidates.extend(results)
                    # We continue to collect candidates from all strategies for Reranking
                    # Or we can stop early. For better reranking, collecting more is better.
                    # However, strictly per current logic, we returned early.
                    # To support Reranking, we should collect at least a pool.
                    # Let's break if we have enough strict results.
                    if isinstance(strategy, StrictVectorStrategy) and len(results) >= 3:
                        break
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")
                continue

        if not candidates:
            return []

        # 3. Reranking Phase
        try:
            logger.info(f"✨ Reranking {len(candidates)} candidates...")

            # Convert SearchResult back to NodeWithScore for Reranker
            # This is a bit awkward mapping but necessary since Reranker expects LlamaIndex objects
            nodes = [
                NodeWithScore(
                    node=TextNode(text=c.content, metadata=c.metadata),
                    score=c.score or 0.5
                )
                for c in candidates
            ]

            # Rerank using the refined query (it has better context) OR original query (user intent)
            # Refined query is usually better for semantic match.
            reranked_nodes = get_reranker().rerank(refined_q, nodes, top_n=5)

            # Convert back to SearchResult
            final_results = []
            for n in reranked_nodes:
                final_results.append(
                    SearchResult(
                        content=n.node.get_content(),
                        metadata=n.node.metadata,
                        score=n.score,
                        source="reranker"
                    )
                )

            logger.info(f"🎉 Returning {len(final_results)} reranked results.")
            return final_results

        except Exception as e:
            logger.error(f"Reranking integration failed: {e}. Returning raw candidates.")
            return candidates[:5]


# Singleton
search_orchestrator = SearchOrchestrator()
