from typing import List, Optional
import os
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.retrievers import BaseRetriever
from llama_index.vector_stores.supabase import SupabaseVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Initialize Embedding Model (Singleton to avoid reload)
# Using the model specified in memory: intfloat/multilingual-e5-small
_EMBED_MODEL = None

def get_embedding_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-small")
    return _EMBED_MODEL

class LlamaIndexRetriever:
    def __init__(self, db_url: str, collection_name: str = "vectors"):
        self.db_url = db_url
        self.collection_name = collection_name
        self.embed_model = get_embedding_model()

        # Ensure compatibility with 'vecs' (psycopg2)
        postgres_url = db_url.replace("+asyncpg", "")

        self.vector_store = SupabaseVectorStore(
            postgres_connection_string=postgres_url,
            collection_name=collection_name
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model
        )

    def search(self, query: str, limit: int = 5, filters: Optional[dict] = None) -> List[NodeWithScore]:
        """
        Semantic search using LlamaIndex with support for Metadata Filters.
        """
        llama_filters = None

        if filters:
            match_filters = []
            if "year" in filters and filters["year"]:
                match_filters.append(ExactMatchFilter(key="year", value=filters["year"]))
            if "subject" in filters and filters["subject"]:
                # Normalize/Fuzzy match might be needed upstream, assuming refined subject here
                match_filters.append(ExactMatchFilter(key="subject", value=filters["subject"]))

            if match_filters:
                llama_filters = MetadataFilters(filters=match_filters)

        retriever = self.index.as_retriever(
            similarity_top_k=limit,
            filters=llama_filters
        )

        nodes = retriever.retrieve(query)
        return nodes

# Global instance manager
_RETRIEVER_INSTANCE = None

def get_retriever(db_url: str) -> LlamaIndexRetriever:
    global _RETRIEVER_INSTANCE
    if _RETRIEVER_INSTANCE is None:
        _RETRIEVER_INSTANCE = LlamaIndexRetriever(db_url)
    return _RETRIEVER_INSTANCE
