import asyncio

from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.logging import get_logger

logger = get_logger("verification")


async def verify():
    print("🔍 Verifying Knowledge Graph in Supabase...")
    async with async_session_factory() as session:
        # Check Nodes
        result_nodes = await session.execute(text("SELECT count(*) FROM knowledge_nodes"))
        count_nodes = result_nodes.scalar()
        print(f"✅ Nodes Count: {count_nodes}")

        # Check Edges
        result_edges = await session.execute(text("SELECT count(*) FROM knowledge_edges"))
        count_edges = result_edges.scalar()
        print(f"✅ Edges Count: {count_edges}")

        # Sample Node
        sample = await session.execute(text("SELECT name, label FROM knowledge_nodes LIMIT 5"))
        print("\n📋 Sample Nodes:")
        for row in sample:
            print(f" - {row[1]}: {row[0]}")


if __name__ == "__main__":
    asyncio.run(verify())
