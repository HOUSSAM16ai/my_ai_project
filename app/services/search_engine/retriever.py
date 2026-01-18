from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.supabase import SupabaseVectorStore
    from llama_index.core.schema import NodeWithScore

def _placeholder_from_vector_store(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("لم يتم تحميل LlamaIndex بعد.")


_VECTOR_STORE_INDEX_PLACEHOLDER_METHOD = _placeholder_from_vector_store


class _VectorStoreIndexPlaceholder:
    """بديل أولي لضمان توفر الواجهة قبل تحميل LlamaIndex."""

    from_vector_store = staticmethod(_placeholder_from_vector_store)


class _SupabaseVectorStorePlaceholder:
    """بديل أولي لمخزن المتجهات قبل تحميل الاعتمادات."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError("لم يتم تحميل LlamaIndex بعد.")


class _HuggingFaceEmbeddingPlaceholder:
    """بديل أولي لنموذج التضمين قبل تحميل الاعتمادات."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError("لم يتم تحميل LlamaIndex بعد.")


_EMBED_MODEL: HuggingFaceEmbedding | None = None

VectorStoreIndex = _VectorStoreIndexPlaceholder
SupabaseVectorStore = _SupabaseVectorStorePlaceholder
HuggingFaceEmbedding = _HuggingFaceEmbeddingPlaceholder

def _load_llama_index_dependencies() -> None:
    """يقوم هذا التابع بتحميل اعتمادات LlamaIndex عند الحاجة فقط."""
    global VectorStoreIndex
    global SupabaseVectorStore
    global HuggingFaceEmbedding
    if importlib.util.find_spec("llama_index") is None:
        return
    if (
        VectorStoreIndex is _VectorStoreIndexPlaceholder
        and VectorStoreIndex.from_vector_store is _VECTOR_STORE_INDEX_PLACEHOLDER_METHOD
    ):
        from llama_index.core import VectorStoreIndex as _VectorStoreIndex

        VectorStoreIndex = _VectorStoreIndex
    if SupabaseVectorStore is _SupabaseVectorStorePlaceholder:
        from llama_index.vector_stores.supabase import (
            SupabaseVectorStore as _SupabaseVectorStore,
        )

        SupabaseVectorStore = _SupabaseVectorStore
    if HuggingFaceEmbedding is _HuggingFaceEmbeddingPlaceholder:
        from llama_index.embeddings.huggingface import (
            HuggingFaceEmbedding as _HuggingFaceEmbedding,
        )

        HuggingFaceEmbedding = _HuggingFaceEmbedding

def get_embedding_model():
    """يعيد نموذج التضمين مع ضمان التهيئة الواحدة لتقليل التكلفة."""
    global _EMBED_MODEL
    _load_llama_index_dependencies()
    if _EMBED_MODEL is None and HuggingFaceEmbedding is not _HuggingFaceEmbeddingPlaceholder:
        _EMBED_MODEL = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-small")
    return _EMBED_MODEL

class LlamaIndexRetriever:
    """مسؤول عن تهيئة محرك الاسترجاع الدلالي اعتماداً على LlamaIndex."""

    def __init__(self, db_url: str, collection_name: str = "vectors"):
        """ينشئ مسترجعاً دلالياً مرتبطاً بمخزن المتجهات في Supabase."""
        _load_llama_index_dependencies()
        self.db_url = db_url
        self.collection_name = collection_name
        self.embed_model = get_embedding_model()

        # Connect to Supabase Vector Store
        # Note: generic SupabaseVectorStore usage requires postgres_connection_string
        # We use the same URL provided by user.
        if SupabaseVectorStore is _SupabaseVectorStorePlaceholder:
            raise RuntimeError("تعذر تحميل SupabaseVectorStore من مكتبة LlamaIndex.")
        self.vector_store = SupabaseVectorStore(
            postgres_connection_string=db_url,
            collection_name=collection_name
        )
        if (
            VectorStoreIndex is _VectorStoreIndexPlaceholder
            and VectorStoreIndex.from_vector_store is _VECTOR_STORE_INDEX_PLACEHOLDER_METHOD
        ):
            raise RuntimeError("تعذر تحميل VectorStoreIndex من مكتبة LlamaIndex.")
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model
        )

    def search(
        self,
        query: str,
        limit: int = 5,
        filters: dict[str, str | int | float] | None = None,
    ) -> list[NodeWithScore]:
        """ينفذ بحثاً دلالياً مع إمكانية تمرير مرشحات وصفية اختيارية."""
        # Configure retriever
        # We can add metadata filters here if needed using exact_match_metadata
        # But for now we rely on the semantic match and post-filtering if necessary.

        # Note: filters in SupabaseVectorStore are a bit specific.
        # If we need strict filtering (year=2024), we should pass it.
        # However, LlamaIndex standard retriever interface might need MetadataFilters.

        retriever = self.index.as_retriever(similarity_top_k=limit)
        nodes = retriever.retrieve(query)
        return nodes

_RETRIEVER_INSTANCE: LlamaIndexRetriever | None = None

def get_retriever(db_url: str) -> LlamaIndexRetriever:
    """يعيد نسخة مشتركة من المسترجع لتقليل كلفة التهيئة."""
    global _RETRIEVER_INSTANCE
    if _RETRIEVER_INSTANCE is None:
        _RETRIEVER_INSTANCE = LlamaIndexRetriever(db_url)
    return _RETRIEVER_INSTANCE
