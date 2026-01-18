import os
import sys
import logging
from sqlalchemy import create_engine, text

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.settings.base import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_vector_db():
    settings = get_settings()
    # Force Sync URL
    db_url = settings.DATABASE_URL.replace("+asyncpg", "")

    # Supabase Pooler usually needs SSL
    # For psycopg2, we usually pass connect_args={'sslmode': 'require'}
    # If the URL already has parameters, we should be careful.

    # Strip existing query params that might cause issues if we add them manually
    if "?" in db_url:
        base_url = db_url.split("?")[0]
    else:
        base_url = db_url

    logger.info(f"Connecting to DB: {base_url.split('@')[-1]}")

    # Pass sslmode via connect_args for psycopg2
    engine = create_engine(
        base_url,
        echo=False,
        connect_args={'sslmode': 'require'}
    )

    with engine.connect() as conn:
        logger.info("Enabling vector extension...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        except Exception as e:
            logger.warning(f"Extension creation failed: {e}")

        logger.info("Re-creating 'vectors' table with 384 dimensions (e5-small)...")
        conn.execute(text("DROP TABLE IF EXISTS vectors CASCADE"))
        conn.commit()

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vectors (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT,
                metadata JSONB,
                embedding VECTOR(384)
            )
        """))
        conn.commit()

        logger.info("Creating 'match_vectors' function...")
        conn.execute(text("DROP FUNCTION IF EXISTS match_vectors"))

        conn.execute(text("""
            CREATE OR REPLACE FUNCTION match_vectors(
                query_embedding VECTOR(384),
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
        conn.commit()

        logger.info("Creating Index...")
        try:
             conn.execute(text("""
                CREATE INDEX IF NOT EXISTS vectors_embedding_idx
                ON vectors
                USING hnsw (embedding vector_cosine_ops);
            """))
             conn.commit()
        except Exception as e:
             logger.warning(f"Index creation warning: {e}")

    logger.info("Vector DB Setup Complete.")
    engine.dispose()

if __name__ == "__main__":
    setup_vector_db()
