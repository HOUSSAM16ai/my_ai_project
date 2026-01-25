import asyncio
import os
from sqlalchemy import text
from app.core.database import async_session_factory
from app.services.search_engine.retriever import get_embedding_model
from app.core.logging import get_logger

# Mute noisy logs
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = get_logger("super-search")

async def search_knowledge_graph(query: str):
    print(f"\n🔎 Query: '{query}'")
    print("-" * 50)

    # 1. Generate Embedding (The Utilities: BGE-M3)
    embed_model = get_embedding_model()
    query_embedding = embed_model.get_text_embedding(query)

    # 2. Vector Search (The Serving Layer: Supabase pgvector)
    async with async_session_factory() as session:
        # Cosine similarity search using <=> operator (distance)
        # 1 - distance = similarity
        stmt = text("""
            SELECT name, label, content, 1 - (embedding <=> :embedding) as similarity
            FROM knowledge_nodes
            ORDER BY embedding <=> :embedding
            LIMIT 5
        """)

        # Format embedding as string for SQL
        emb_str = str(query_embedding)

        result = await session.execute(stmt, {"embedding": emb_str})
        rows = result.fetchall()

        if not rows:
            print("❌ No results found.")
            return

        # 3. Intelligent Display (The Reasoning)
        for i, row in enumerate(rows):
            name, label, content, similarity = row

            # Simple heuristic: If user asked for questions, warn if solution is found
            is_solution = label and "Solution" in label
            warning = "⚠️ (Solution Detected)" if is_solution else ""

            print(f"{i+1}. [{label}] {name} {warning}")
            print(f"   Score: {similarity:.4f}")
            print(f"   Content: {content[:150]}...") # Truncate content
            print("")

async def main():
    queries = [
        "تمرين 1 رياضيات 2024 علوم تجريبية الموضوع 1",
        "اريد اسئلة التمرين الاول باك 2024 رياضيات",
        "Bac 2024 Math Experimental Subject 1 Ex 1 questions"
    ]

    for q in queries:
        await search_knowledge_graph(q)

if __name__ == "__main__":
    asyncio.run(main())
