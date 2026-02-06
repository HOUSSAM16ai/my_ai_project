import functools

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore


@functools.lru_cache(maxsize=1)
def get_embedding_model():
    """
    Returns the singleton embedding model instance.
    Cached to prevent reloading heavy weights.
    Using BAAI/bge-m3 as requested for "The Ultimate Super Stack".
    """
    return HuggingFaceEmbedding(model_name="BAAI/bge-m3")


class LlamaIndexRetriever:
    def __init__(self, db_url: str, collection_name: str = "vectors"):
        self.db_url = db_url
        self.collection_name = collection_name
        self.embed_model = get_embedding_model()

        # Ensure compatibility with 'vecs' (psycopg2)
        postgres_url = db_url.replace("+asyncpg", "")

        self.vector_store = SupabaseVectorStore(
            postgres_connection_string=postgres_url, collection_name=collection_name
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store, embed_model=self.embed_model
        )

    def search(
        self, query: str, limit: int = 5, filters: dict | None = None
    ) -> list[NodeWithScore]:
        """
        Semantic search using LlamaIndex with support for Metadata Filters.
        """
        llama_filters = None

        if filters:
            match_filters = []
            if filters.get("year"):
                match_filters.append(ExactMatchFilter(key="year", value=filters["year"]))
            if filters.get("subject"):
                # Normalize/Fuzzy match might be needed upstream, assuming refined subject here
                match_filters.append(ExactMatchFilter(key="subject", value=filters["subject"]))

            if match_filters:
                llama_filters = MetadataFilters(filters=match_filters)

        retriever = self.index.as_retriever(similarity_top_k=limit, filters=llama_filters)

        return retriever.retrieve(query)


@functools.lru_cache(maxsize=8)
def get_retriever(db_url: str) -> LlamaIndexRetriever:
    """
    Factory to get or create a LlamaIndexRetriever instance.
    Cached by db_url to allow multiple database connections if needed,
    while avoiding re-initialization for the same DB.
    """
    return LlamaIndexRetriever(db_url)
