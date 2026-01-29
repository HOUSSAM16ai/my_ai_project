"""
Super Search Orchestrator - منسق البحث الخارق.
-----------------------------------------------
يوفر بحثاً قوياً يعمل مع أي صياغة للسؤال.

المميزات:
1. Multi-Query Search: تنفيذ البحث بجميع الـ variations بالتوازي
2. Score Fusion: دمج النتائج من استراتيجيات متعددة
3. Never-Empty Strategy: إذا فشل كل شيء، يُرجع أقرب محتوى
4. Aggressive Fallback: محاولات متعددة مع تخفيف الفلاتر
"""

import asyncio
import os
from collections import defaultdict

from app.core.logging import get_logger
from app.services.search_engine.fallback_expander import FallbackQueryExpander
from app.services.search_engine.models import SearchFilters, SearchRequest, SearchResult
from app.services.search_engine.query_refiner import get_refined_query
from app.services.search_engine.strategies import (
    KeywordStrategy,
    RelaxedVectorStrategy,
    SearchStrategy,
    StrictVectorStrategy,
)

logger = get_logger("super-search")


class SuperSearchOrchestrator:
    """
    منسق بحث خارق يضمن إيجاد نتائج دائماً.
    """

    def __init__(self):
        self.strategies: list[SearchStrategy] = [
            StrictVectorStrategy(),
            RelaxedVectorStrategy(),
            KeywordStrategy(),
        ]

    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """
        البحث الخارق - يضمن إيجاد نتائج مهما كانت الصياغة.
        """
        original_q = request.q
        if not original_q:
            return []

        logger.info(f"🚀 Super Search started for: '{original_q}'")

        # 1. Generate ALL query variations
        all_queries = self._generate_all_queries(original_q)
        logger.info(f"📝 Generated {len(all_queries)} query variations")

        # 2. Try DSPy refinement if available
        refined_filters = await self._try_dspy_refinement(original_q, request.filters)
        request.filters = refined_filters

        # 3. Execute multi-strategy search
        results = await self._multi_strategy_search(all_queries, request)

        if results:
            logger.info(f"✅ Found {len(results)} results")
            return results

        # 4. Aggressive Fallback - relax ALL filters
        logger.warning("⚠️ No results found, trying aggressive fallback...")
        results = await self._aggressive_fallback(all_queries, request)

        if results:
            logger.info(f"🔄 Aggressive fallback found {len(results)} results")
            return results

        # 5. Last Resort - search with just keywords
        logger.warning("🆘 Last resort: searching with minimal keywords...")
        results = await self._last_resort_search(original_q, request.limit)

        logger.info(f"🏁 Final result: {len(results)} items")
        return results

    def _generate_all_queries(self, original_q: str) -> list[str]:
        """
        يولّد جميع التنويعات الممكنة للاستعلام.
        """
        queries = [original_q]

        # Add FallbackExpander variations
        variations = FallbackQueryExpander.generate_variations(original_q)
        for v in variations:
            if v and v not in queries:
                queries.append(v)

        # Add keyword-only version (extract searchable keywords)
        keywords = self._extract_keywords(original_q)
        if keywords and keywords not in queries:
            queries.append(keywords)

        return queries

    def _extract_keywords(self, q: str) -> str:
        """
        يستخرج الكلمات المفتاحية المهمة فقط.
        """
        words = q.split()
        important_words = []

        for word in words:
            word_clean = word.strip()
            # Keep if it's a searchable keyword
            if (
                word_clean in FallbackQueryExpander.SEARCHABLE_KEYWORDS
                or (word_clean.isdigit() and len(word_clean) == 4)
                or word_clean
                in {
                    "٢٠٢٤",
                    "٢٠٢٣",
                    "٢٠٢٢",
                }
            ):
                important_words.append(word_clean)

        return " ".join(important_words)

    async def _try_dspy_refinement(self, query: str, filters: SearchFilters) -> SearchFilters:
        """
        يحاول تحسين الفلاتر باستخدام DSPy.
        """
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return filters

        try:
            dspy_result = await asyncio.to_thread(get_refined_query, query, api_key)

            if isinstance(dspy_result, dict):
                if dspy_result.get("year"):
                    filters.year = dspy_result["year"]
                if dspy_result.get("subject"):
                    filters.subject = dspy_result["subject"]
                if dspy_result.get("branch"):
                    filters.branch = dspy_result["branch"]

                logger.info(f"🧠 DSPy extracted: {filters.model_dump(exclude_none=True)}")

        except Exception as e:
            logger.warning(f"⚠️ DSPy refinement failed: {e}")

        return filters

    async def _multi_strategy_search(
        self, queries: list[str], request: SearchRequest
    ) -> list[SearchResult]:
        """
        ينفذ البحث بجميع الاستراتيجيات والاستعلامات بالتوازي.
        """
        tasks = []

        for strategy in self.strategies:
            for query in queries[:3]:  # Limit to avoid too many parallel calls
                req_copy = SearchRequest(
                    q=query,
                    filters=request.filters.model_copy(),
                    limit=request.limit,
                )
                tasks.append(self._execute_strategy(strategy, req_copy))

        # Execute all in parallel
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge and deduplicate
        return self._merge_results(all_results)

    async def _execute_strategy(
        self, strategy: SearchStrategy, request: SearchRequest
    ) -> list[SearchResult]:
        """
        ينفذ استراتيجية واحدة مع معالجة الأخطاء.
        """
        try:
            return await strategy.execute(request)
        except Exception as e:
            logger.warning(f"Strategy {strategy.name} failed: {e}")
            return []

    def _merge_results(
        self, all_results: list[list[SearchResult] | Exception]
    ) -> list[SearchResult]:
        """
        يدمج النتائج ويزيل التكرار مع الحفاظ على الترتيب.
        """
        seen_ids: set[str] = set()
        merged: list[SearchResult] = []
        score_map: dict[str, float] = defaultdict(float)

        for result_list in all_results:
            if isinstance(result_list, Exception):
                continue

            for result in result_list:
                # Score fusion: increase score for repeated appearances
                score_map[result.id] += 1.0

                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    merged.append(result)

        # Sort by fused score (number of times appeared)
        merged.sort(key=lambda r: score_map[r.id], reverse=True)

        return merged

    async def _aggressive_fallback(
        self, queries: list[str], request: SearchRequest
    ) -> list[SearchResult]:
        """
        يحاول البحث بدون أي فلاتر.
        """
        relaxed_request = SearchRequest(
            q=queries[0] if queries else None,
            filters=SearchFilters(),  # Empty filters
            limit=request.limit,
        )

        # Try relaxed vector strategy
        relaxed_strategy = RelaxedVectorStrategy()
        results = await self._execute_strategy(relaxed_strategy, relaxed_request)

        if results:
            return results

        # Try keyword strategy with variations
        keyword_strategy = KeywordStrategy()
        for query in queries:
            relaxed_request.q = query
            results = await self._execute_strategy(keyword_strategy, relaxed_request)
            if results:
                return results

        return []

    async def _last_resort_search(self, original_q: str, limit: int) -> list[SearchResult]:
        """
        آخر محاولة: البحث بكلمة واحدة فقط.
        """
        from app.services.content.service import content_service

        # Extract just the most important keyword
        keywords = self._extract_keywords(original_q)
        if not keywords:
            # Try just the first meaningful word
            words = [w for w in original_q.split() if len(w) > 2]
            if words:
                keywords = words[0]

        if not keywords:
            return []

        try:
            # Search with single keyword, no filters
            results = await content_service.search_content(
                q=keywords,
                limit=limit,
            )

            return [SearchResult(**r, strategy="Last Resort") for r in results]
        except Exception as e:
            logger.error(f"Last resort search failed: {e}")
            return []


# Singleton
super_search_orchestrator = SuperSearchOrchestrator()
