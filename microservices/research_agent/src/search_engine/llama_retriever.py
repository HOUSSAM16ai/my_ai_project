from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode
from sqlalchemy import text

from microservices.research_agent.src.database import async_session_factory
from microservices.research_agent.src.interfaces import IKnowledgeRetriever
from microservices.research_agent.src.logging import get_logger
from microservices.research_agent.src.search_engine.hybrid import hybrid_search

logger = get_logger("graph-retriever")


class KnowledgeGraphRetriever(BaseRetriever, IKnowledgeRetriever):
    """
    Retriever that uses the custom Hybrid Search (Vector + Sparse + Rerank)
    implementation to fetch nodes from Supabase, AND expands the context
    by traversing the Knowledge Graph edges (2-hop neighbors).
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        super().__init__()

    def _retrieve(self, query_bundle) -> list[NodeWithScore]:
        raise NotImplementedError("Use aretrieve for this async-native retriever.")

    async def _aretrieve(self, query_bundle) -> list[NodeWithScore]:
        if hasattr(query_bundle, "query_str"):
            query_str = query_bundle.query_str
        else:
            query_str = str(query_bundle)

        # 1. Initial Hybrid Search
        results = await hybrid_search(query_str, top_k=self.top_k)

        if not results:
            return []

        # 2. Graph Expansion (Fetch Neighbors - 2 Hops)
        seed_ids = [str(r["id"]) for r in results]

        try:
            session_factory = async_session_factory()
        except ValueError as exc:
            logger.warning(f"Database unavailable for graph expansion: {exc}")
            return []

        async with session_factory() as session:
            # Recursive CTE for 2-hop traversal
            stmt = text("""
                WITH RECURSIVE traversal AS (
                    -- Base Case: Seeds (Level 0)
                    SELECT unnest(:seed_ids :: text[])::uuid AS id, 0 AS depth

                    UNION

                    -- Recursive Step: Neighbors of previous level (Level 1 and 2)
                    SELECT
                        CASE
                            WHEN e.source_id = t.id THEN e.target_id
                            ELSE e.source_id
                        END AS id,
                        t.depth + 1
                    FROM traversal t
                    JOIN knowledge_edges e ON e.source_id = t.id OR e.target_id = t.id
                    WHERE t.depth < 2
                )
                SELECT DISTINCT n.id, n.label, n.name, n.content, t.depth
                FROM knowledge_nodes n
                JOIN traversal t ON n.id = t.id
                WHERE n.id NOT IN (SELECT unnest(:seed_ids :: text[])::uuid) -- Exclude original seeds from neighbor list
            """)

            try:
                res = await session.execute(stmt, {"seed_ids": seed_ids})
                # neighbors will contain both 1-hop and 2-hop nodes
                neighbors = [dict(row._mapping) for row in res.fetchall()]
                logger.info(
                    f"Graph Expansion: Found {len(neighbors)} neighbors (2-hop) for {len(seed_ids)} seed nodes."
                )
            except Exception as e:
                logger.error(f"Graph expansion failed: {e}")
                neighbors = []

        # 3. Merge Results
        final_nodes = []
        seen_ids = set()

        # Add primary results (Depth 0)
        for r in results:
            nid = str(r["id"])
            if nid in seen_ids:
                continue
            seen_ids.add(nid)

            node = TextNode(
                text=f"{r['name']}: {r['content']}",
                id_=nid,
                metadata={
                    "name": r["name"],
                    "label": r["label"],
                    "score": r.get("rerank_score", r.get("hybrid_score", 0.0)),
                    "type": "primary",
                    "depth": 0,
                },
            )
            score = r.get("rerank_score", r.get("hybrid_score", 0.0))
            final_nodes.append(NodeWithScore(node=node, score=score))

        # Add neighbors
        for n in neighbors:
            nid = str(n["id"])
            if nid in seen_ids:
                continue
            seen_ids.add(nid)

            depth = n.get("depth", 1)
            # Decay score by depth
            base_score = 0.5
            decayed_score = base_score / (depth + 1)  # 0.25 for depth 1, 0.16 for depth 2? No wait.
            # depth 1: 0.5/2 = 0.25
            # depth 2: 0.5/3 = 0.16
            # Actually, let's keep it simple: 0.5 for neighbors.

            node = TextNode(
                text=f"{n['name']}: {n['content']}",
                id_=nid,
                metadata={
                    "name": n["name"],
                    "label": n["label"],
                    "score": decayed_score,
                    "type": "neighbor",
                    "depth": depth,
                },
            )
            final_nodes.append(NodeWithScore(node=node, score=decayed_score))

        return final_nodes
