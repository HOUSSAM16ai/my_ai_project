"""
Graph Expander - توسيع البحث عبر الرسم البياني.
-------------------------------------------------
يستخدم علاقات knowledge_edges لتوسيع نتائج البحث.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from microservices.research_agent.src.database import async_session_factory
from microservices.research_agent.src.logging import get_logger

logger = get_logger("graph-expander")


async def expand_with_neighbors(
    node_ids: list[str],
    hop_count: int = 1,
    limit_per_node: int = 3,
) -> list[dict[str, object]]:
    """
    يوسع نتائج البحث عبر الرسم البياني باستخدام قفزات متعددة.

    Args:
        node_ids: معرّفات العقد الأولية
        hop_count: عدد القفزات المعرفية (1 = مجاور مباشر)
        limit_per_node: حد المجاورين لكل عقدة

    Returns:
        list: قائمة العقد المجاورة مع معلومات العلاقة
    """
    if not node_ids:
        return []

    if hop_count < 1:
        return []

    try:
        session_factory = async_session_factory()
    except ValueError as exc:
        logger.warning(f"Database unavailable for graph expansion: {exc}")
        return []

    try:
        async with session_factory() as session:
            visited = set(node_ids)
            frontier = list(node_ids)
            neighbors: list[dict[str, object]] = []

            for hop in range(1, hop_count + 1):
                hop_neighbors = await _fetch_neighbors(
                    session=session,
                    node_ids=frontier,
                    limit_per_node=limit_per_node,
                )
                if not hop_neighbors:
                    break

                new_frontier: list[str] = []
                for item in hop_neighbors:
                    node_id = str(item.get("id", ""))
                    if not node_id or node_id in visited:
                        continue
                    visited.add(node_id)
                    item["hop"] = hop
                    neighbors.append(item)
                    new_frontier.append(node_id)

                frontier = new_frontier
                if not frontier:
                    break

            logger.info(
                "Graph expansion produced %s neighbors across %s hops.",
                len(neighbors),
                hop_count,
            )
            return neighbors

    except Exception as e:
        logger.warning(f"Graph expansion failed: {e}")
        return []


async def _fetch_neighbors(
    *, session: AsyncSession, node_ids: list[str], limit_per_node: int
) -> list[dict[str, object]]:
    """
    يجلب الجيران المباشرين لعقد محددة ضمن حدود مضبوطة.
    """
    if not node_ids:
        return []

    placeholders = [f":id_{i}" for i in range(len(node_ids))]
    params = {f"id_{i}": nid for i, nid in enumerate(node_ids)}
    params["limit"] = limit_per_node * len(node_ids)

    query = text(f"""
        SELECT DISTINCT
            n.id,
            n.name,
            n.label,
            n.content,
            e.relationship_type,
            e.weight
        FROM knowledge_edges e
        JOIN knowledge_nodes n ON (
            (e.source_id IN ({", ".join(placeholders)}) AND e.target_id = n.id)
            OR
            (e.target_id IN ({", ".join(placeholders)}) AND e.source_id = n.id)
        )
        WHERE n.id NOT IN ({", ".join(placeholders)})
        ORDER BY e.weight DESC NULLS LAST
        LIMIT :limit
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()
    neighbors: list[dict[str, object]] = []
    for row in rows:
        neighbors.append(
            {
                "id": row[0],
                "name": row[1],
                "label": row[2],
                "content": row[3],
                "relationship": row[4],
                "weight": row[5],
            }
        )
    return neighbors


async def find_related_content(
    content_ids: list[str],
    relationship_types: list[str] | None = None,
) -> list[str]:
    """
    يجد المحتوى المرتبط عبر العلاقات في الرسم البياني.

    Args:
        content_ids: معرّفات المحتوى الأولية
        relationship_types: أنواع العلاقات المطلوبة (اختياري)

    Returns:
        list: معرّفات المحتوى المرتبط
    """
    if not content_ids:
        return []

    try:
        session_factory = async_session_factory()
    except ValueError as exc:
        logger.warning(f"Database unavailable for related content: {exc}")
        return []

    try:
        async with session_factory() as session:
            # First, find knowledge_nodes linked to these content_items
            placeholders = [f":cid_{i}" for i in range(len(content_ids))]
            params = {f"cid_{i}": cid for i, cid in enumerate(content_ids)}

            # Find nodes that have these content_ids in their metadata
            node_query = text(f"""
                SELECT id FROM knowledge_nodes
                WHERE metadata->>'content_id' IN ({", ".join(placeholders)})
            """)

            result = await session.execute(node_query, params)
            node_ids = [row[0] for row in result.fetchall()]

            if not node_ids:
                return []

            # Get neighbors
            neighbors = await expand_with_neighbors(node_ids)

            # Extract content_ids from neighbors
            related_ids = []
            for n in neighbors:
                # The content might store content_id in the name or we can derive it
                if n.get("name"):
                    related_ids.append(n["name"])

            return related_ids

    except Exception as e:
        logger.warning(f"Related content search failed: {e}")
        return []


async def enrich_search_with_graph(
    initial_results: list[dict[str, object]],
    max_expansion: int = 5,
) -> list[dict[str, object]]:
    """
    يثري نتائج البحث بالمحتوى المرتبط من الرسم البياني.

    Args:
        initial_results: النتائج الأولية من البحث
        max_expansion: الحد الأقصى للتوسيع

    Returns:
        list: النتائج الموسعة
    """
    if not initial_results:
        return []

    content_ids = [r.get("id") for r in initial_results if r.get("id")]

    # Get related content
    related_ids = await find_related_content(content_ids[:3])  # Limit input

    if not related_ids:
        return initial_results

    # Fetch full content for related items
    from microservices.research_agent.src.content.service import content_service

    try:
        related_content = await content_service.search_content(
            content_ids=related_ids[:max_expansion],
            limit=max_expansion,
        )

        # Mark as graph-expanded
        for item in related_content:
            item["source"] = "graph_expansion"

        # Combine: original first, then expanded
        seen_ids = {r.get("id") for r in initial_results}
        combined = list(initial_results)

        for item in related_content:
            if item.get("id") not in seen_ids:
                combined.append(item)
                seen_ids.add(item.get("id"))

        return combined

    except Exception as e:
        logger.warning(f"Graph enrichment failed: {e}")
        return initial_results
