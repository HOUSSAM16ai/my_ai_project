from typing import Any

from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.logging import get_logger
from microservices.research_agent.src.search_engine.reranker import get_reranker
from microservices.research_agent.src.search_engine.retriever import get_embedding_model

logger = get_logger("hybrid-search")


async def hybrid_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Implements a Hybrid Search Strategy:
    1. Dense Retrieval (Vector)
    2. Sparse Retrieval (Keyword/BM25 via tsvector)
    3. Graph Traversal (1-hop expansion) - *Simplified implicitly by vector capturing relations in content*
    4. Reranking (Cross-Encoder)
    """

    # 1. Generate Query Embedding
    embed_model = get_embedding_model()
    query_embedding = embed_model.get_text_embedding(query)
    emb_str = str(query_embedding)

    # 2. Execute Hybrid Query in SQL
    # We fetch a candidate pool larger than top_k to allow reranking to work effectively
    pool_size = top_k * 4

    async with async_session_factory() as session:
        # Combined Query using CTEs
        stmt = text("""
        WITH dense_results AS (
            SELECT id, 1 - (embedding <=> :embedding) as dense_score
            FROM knowledge_nodes
            ORDER BY embedding <=> :embedding
            LIMIT :pool_size
        ),
        sparse_results AS (
            SELECT id, ts_rank(search_vector, plainto_tsquery('simple', :query)) as sparse_score
            FROM knowledge_nodes
            WHERE search_vector @@ plainto_tsquery('simple', :query)
            ORDER BY sparse_score DESC
            LIMIT :pool_size
        ),
        merged_scores AS (
            SELECT
                COALESCE(d.id, s.id) as id,
                COALESCE(d.dense_score, 0.0) as dense_score,
                COALESCE(s.sparse_score, 0.0) as sparse_score
            FROM dense_results d
            FULL OUTER JOIN sparse_results s ON d.id = s.id
        )
        SELECT
            m.id,
            n.label,
            n.name,
            n.content,
            m.dense_score,
            m.sparse_score
        FROM merged_scores m
        JOIN knowledge_nodes n ON m.id = n.id
        """)

        result = await session.execute(
            stmt, {"embedding": emb_str, "query": query, "pool_size": pool_size}
        )
        candidates = [dict(row._mapping) for row in result.fetchall()]

    if not candidates:
        return []

    # 3. Score Fusion (Weighted Sum)
    # Adjust weights: Semantic is usually stronger for "understanding", Keyword for "precision"
    alpha = 0.7  # Weight for Dense
    beta = 0.3  # Weight for Sparse (normalized roughly)

    # Normalize sparse scores (simple max-min scaling per query)
    max_sparse = max((c["sparse_score"] for c in candidates), default=1.0)
    if max_sparse == 0:
        max_sparse = 1.0

    fusion_candidates = []
    for c in candidates:
        # Normalized Sparse
        norm_sparse = c["sparse_score"] / max_sparse

        # Initial Hybrid Score
        hybrid_score = (c["dense_score"] * alpha) + (norm_sparse * beta)

        c["hybrid_score"] = hybrid_score
        c["norm_sparse"] = norm_sparse
        fusion_candidates.append(c)

    # Sort by Hybrid Score desc
    fusion_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)

    # 4. Reranking (The Judge)
    # We take top N from fusion to rerank
    rerank_pool = fusion_candidates[:pool_size]

    try:
        reranker = get_reranker()

        # Prepare pairs for cross-encoder: (query, document_text)
        pairs = [[query, f"{c['name']}: {c['content']}"] for c in rerank_pool]

        # Predict scores
        rerank_scores = reranker.model.predict(pairs)

        # Attach rerank scores
        for i, c in enumerate(rerank_pool):
            c["rerank_score"] = float(rerank_scores[i])

        # Final Sort by Reranker Score
        rerank_pool.sort(key=lambda x: x["rerank_score"], reverse=True)

    except Exception as e:
        logger.warning(f"Reranking failed: {e}. Falling back to hybrid score.")
        # If reranker fails, we stick to hybrid score order

    return rerank_pool[:top_k]
