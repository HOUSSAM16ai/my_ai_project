"""واجهة البحث مع تحميل كسول لتجنب الاعتماد المباشر على مكونات ثقيلة."""

from __future__ import annotations

from .query_refiner import get_refined_query


def get_retriever(*args, **kwargs):  # type: ignore[no-untyped-def]
    """يعيد كائن المسترجع مع تحميل كسول للتبعيات الثقيلة."""
    from .retriever import get_retriever as _get_retriever

    return _get_retriever(*args, **kwargs)


def LlamaIndexRetriever(*args, **kwargs):  # type: ignore[no-untyped-def]
    """ينشئ مسترجع LlamaIndex مع تحميل كسول."""
    from .retriever import LlamaIndexRetriever as _LlamaIndexRetriever

    return _LlamaIndexRetriever(*args, **kwargs)


__all__ = ["LlamaIndexRetriever", "get_refined_query", "get_retriever"]
