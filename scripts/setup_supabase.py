import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.settings.base import get_settings

logging_format = '%(asctime)s - %(levelname)s - %(message)s'
import logging
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)

async def setup_vector_db():
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # Supabase Transaction Pooler (6543) compatibility
    connect_args = {}
    if "postgresql" in db_url or "asyncpg" in db_url:
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        }

    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args=connect_args
    )

    async with engine.begin() as conn:
        logger.info("Enabling vector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        logger.info("Creating 'vectors' table for LlamaIndex...")
        # LlamaIndex default schema usually involves: id, content, metadata, embedding
        # We use a generic table name 'vectors'
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vectors (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT,
                metadata JSONB,
                embedding VECTOR(1536) -- OpenAI embedding dimension
            )
        """))

        logger.info("Creating 'match_vectors' function...")
        # Standard match function for LlamaIndex Supabase Vector Store
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION match_vectors(
                query_embedding VECTOR(1536),
                match_threshold FLOAT,
                match_count INT,
                filter JSONB DEFAULT '{}'
            )
            RETURNS TABLE (
                id UUID,
                content TEXT,
                metadata JSONB,
                similarity FLOAT
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    v.id,
                    v.content,
                    v.metadata,
                    1 - (v.embedding <=> query_embedding) AS similarity
                FROM
                    vectors v
                WHERE
                    1 - (v.embedding <=> query_embedding) > match_threshold
                    AND (filter IS NULL OR v.metadata @> filter)
                ORDER BY
                    v.embedding <=> query_embedding
                LIMIT match_count;
            END;
            $$;
        """))

        # Create HNSW index for performance
        logger.info("Creating HNSW index (this might take a while if table is large)...")
        try:
             await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS vectors_embedding_idx
                ON vectors
                USING hnsw (embedding vector_cosine_ops);
            """))
        except Exception as e:
            logger.warning(f"Could not create HNSW index (possibly insufficient privileges or data): {e}")

    logger.info("Vector DB Setup Complete.")
    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup_vector_db())
