from __future__ import annotations

import importlib
import importlib.util

# Initialize Embedding Model (Singleton to avoid reload)
# Using the model specified in memory: intfloat/multilingual-e5-small
_EMBED_MODEL = None


def get_embedding_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _components = _load_llama_components()
        # Using BAAI/bge-m3 as requested for "The Ultimate Super Stack"
        # M3 supports multi-linguality (Arabic/English) and high performance.
        _EMBED_MODEL = _components["HuggingFaceEmbedding"](model_name="BAAI/bge-m3")
    return _EMBED_MODEL


class LlamaIndexRetriever:
    def __init__(self, db_url: str, collection_name: str = "vectors"):
        components = _load_llama_components()
        self.db_url = db_url
        self.collection_name = collection_name
        self.embed_model = get_embedding_model()

        # Ensure compatibility with 'vecs' (psycopg2)
        postgres_url = db_url.replace("+asyncpg", "")

        self.vector_store = components["SupabaseVectorStore"](
            postgres_connection_string=postgres_url, collection_name=collection_name
        )
        self.index = components["VectorStoreIndex"].from_vector_store(
            vector_store=self.vector_store, embed_model=self.embed_model
        )

    def search(
        self, query: str, limit: int = 5, filters: dict | None = None
    ) -> list[object]:
        """
        Semantic search using LlamaIndex with support for Metadata Filters.
        """
        components = _load_llama_components()
        llama_filters = None

        if filters:
            match_filters = []
            if filters.get("year"):
                match_filters.append(
                    components["ExactMatchFilter"](key="year", value=filters["year"])
                )
            if filters.get("subject"):
                # Normalize/Fuzzy match might be needed upstream, assuming refined subject here
                match_filters.append(
                    components["ExactMatchFilter"](key="subject", value=filters["subject"])
                )

            if match_filters:
                llama_filters = components["MetadataFilters"](filters=match_filters)

        retriever = self.index.as_retriever(similarity_top_k=limit, filters=llama_filters)

        return retriever.retrieve(query)


def _load_llama_components() -> dict[str, object]:
    """يحمل مكونات LlamaIndex عند توفرها فقط."""
    if importlib.util.find_spec("llama_index") is None:
        raise RuntimeError("LlamaIndex غير متاح في البيئة الحالية.")
    required_modules = [
        "llama_index.core",
        "llama_index.core.schema",
        "llama_index.core.vector_stores",
        "llama_index.embeddings.huggingface",
        "llama_index.vector_stores.supabase",
    ]
    for module in required_modules:
        if importlib.util.find_spec(module) is None:
            raise RuntimeError("مكونات LlamaIndex غير متاحة بشكل كامل.")
    return {
        "VectorStoreIndex": importlib.import_module("llama_index.core").VectorStoreIndex,
        "ExactMatchFilter": importlib.import_module(
            "llama_index.core.vector_stores"
        ).ExactMatchFilter,
        "MetadataFilters": importlib.import_module(
            "llama_index.core.vector_stores"
        ).MetadataFilters,
        "HuggingFaceEmbedding": importlib.import_module(
            "llama_index.embeddings.huggingface"
        ).HuggingFaceEmbedding,
        "SupabaseVectorStore": importlib.import_module(
            "llama_index.vector_stores.supabase"
        ).SupabaseVectorStore,
    }


# Global instance manager
_RETRIEVER_INSTANCE = None


def get_retriever(db_url: str) -> LlamaIndexRetriever:
    global _RETRIEVER_INSTANCE
    if _RETRIEVER_INSTANCE is None:
        _RETRIEVER_INSTANCE = LlamaIndexRetriever(db_url)
    return _RETRIEVER_INSTANCE
