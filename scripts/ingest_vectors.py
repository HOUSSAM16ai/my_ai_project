import asyncio
import os
import sys
import logging
from typing import List, Dict

# Add project root to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.settings.base import get_settings

# LlamaIndex Imports
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.supabase import SupabaseVectorStore
# Using HuggingFace Embedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_content_items(limit=1000, offset=0) -> List[Dict]:
    settings = get_settings()
    db_url = settings.DATABASE_URL
    connect_args = {}
    if "postgresql" in db_url or "asyncpg" in db_url:
        connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}

    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)

    items = []
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT id, title, md_content, year, subject, set_name, level
            FROM content_items
            ORDER BY year DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset})

        rows = result.fetchall()
        for row in rows:
            items.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "year": row[3],
                "subject": row[4],
                "set_name": row[5],
                "level": row[6]
            })

    await engine.dispose()
    return items

def create_documents(items: List[Dict]) -> List[Document]:
    documents = []
    for item in items:
        metadata = {
            "content_id": item["id"],
            "year": item["year"],
            "subject": item["subject"],
            "set_name": item["set_name"],
            "level": item["level"],
            "title": item["title"]
        }

        if "علوم تجريبية" in item["title"] or "experimental" in item["title"].lower():
             metadata["branch"] = "experimental_sciences"
        elif "تقني رياضي" in item["title"] or "technical" in item["title"].lower():
             metadata["branch"] = "math_tech"
        elif "رياضيات" in item["title"] or "mathematics" in item["title"].lower():
             metadata["branch"] = "mathematics"

        doc = Document(
            text=item["content"],
            metadata=metadata,
            excluded_llm_metadata_keys=["content_id"],
            excluded_embed_metadata_keys=["content_id"]
        )
        documents.append(doc)
    return documents

async def ingest_vectors():
    settings = get_settings()

    # 1. Setup Vector Store (Sync for LlamaIndex)
    logger.info("Initializing Supabase Vector Store...")
    sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
    if "?" in sync_db_url:
        sync_db_url = sync_db_url.split("?")[0]

    # SupabaseVectorStore uses postgres_connection_string
    vector_store = SupabaseVectorStore(
        postgres_connection_string=sync_db_url,
        collection_name="vectors",
        dimension=384 # Matches multilingual-e5-small
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 2. Fetch Data
    logger.info("Fetching content from SQL DB...")
    items = await fetch_content_items()
    logger.info(f"Fetched {len(items)} items.")

    if not items:
        return

    documents = create_documents(items)

    # 3. Create Index
    logger.info("Loading Embedding Model (intfloat/multilingual-e5-small)...")
    # This will download the model (~500MB) on first run
    embed_model = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-small")

    logger.info("Indexing...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )

    logger.info("Ingestion Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(ingest_vectors())
