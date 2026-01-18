import os
import logging
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.supabase import SupabaseVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.schema import NodeWithScore, TextNode

from app.core.settings.base import get_settings
# Import the SQL Service for fallback
from app.services.content.service import get_content_service
from app.services.content.domain import ContentFilter

logger = logging.getLogger(__name__)

class ContentRetriever:
    _instance = None
    _index = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContentRetriever, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        settings = get_settings()

        try:
            sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
            if "?" in sync_db_url:
                sync_db_url = sync_db_url.split("?")[0]

            self.vector_store = SupabaseVectorStore(
                postgres_connection_string=sync_db_url,
                collection_name="vectors",
                dimension=384 # Updated to match e5-small
            )
            # Use Local Embedding (No API Key required)
            logger.info("Loading Embedding Model (intfloat/multilingual-e5-small)...")
            self.embed_model = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-small")

            self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

            self._index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model
            )
            self._ready = True
        except Exception as e:
            logger.error(f"Failed to initialize Vector Store: {e}")
            self._ready = False

    async def retrieve(self, query: str, filters: Optional[Dict] = None, k: int = 5) -> List[NodeWithScore]:
        """
        Retrieves documents using Semantic Search with a fallback to SQL Search.
        Implementation of 'Planning for Failure'.
        """
        results = []

        # 1. Try Semantic Search
        if self._ready:
            try:
                logger.info(f"Attempting Semantic Search for: {query}")
                metadata_filters = None
                if filters:
                    ms = []
                    for key, value in filters.items():
                        if value is not None:
                            ms.append(ExactMatchFilter(key=key, value=value))
                    if ms:
                        metadata_filters = MetadataFilters(filters=ms)

                retriever = self._index.as_retriever(
                    similarity_top_k=k,
                    filters=metadata_filters
                )

                results = retriever.retrieve(query)

                if results:
                    return results

                logger.info("Semantic search returned no results.")

            except Exception as e:
                logger.warning(f"Semantic Search Failed: {e}")
                # Fallback proceeds below

        # 2. Fallback to SQL Search (Service Layer)
        logger.info("Falling back to SQL Search...")
        try:
            content_service = get_content_service()

            # Map filters
            sql_filter = ContentFilter(
                q=query,
                year=filters.get("year"),
                subject=filters.get("subject"),
                limit=k
            )

            items = await content_service.search_content(sql_filter)

            nodes = []
            for item in items:
                text_content = f"Title: {item.title}\nID: {item.id}"
                node = NodeWithScore(
                    node=TextNode(
                        text=text_content,
                        metadata={
                            "title": item.title,
                            "year": item.year,
                            "subject": item.subject,
                            "content_id": item.id,
                            "source": "sql_fallback"
                        }
                    ),
                    score=0.5
                )
                nodes.append(node)

            return nodes

        except Exception as e:
            logger.error(f"SQL Fallback also failed: {e}")
            return []

def get_retriever():
    return ContentRetriever()
