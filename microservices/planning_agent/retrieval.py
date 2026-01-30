"""
محرك الاسترجاع والترتيب (Retrieval and Reranking Engine).

تتولى هذه الوحدة فهرسة السياق واسترجاع المعلومات ذات الصلة
باستخدام LlamaIndex واستراتيجية إعادة الترتيب.
"""


from llama_index.core import Document, VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore


class ContextEngine:
    """
    يقوم بفهرسة السياق المؤقت وتوفير قدرات الاسترجاع.
    """
    def __init__(self, context_strings: list[str]):
        self.documents = [Document(text=c) for c in context_strings]
        self.index = VectorStoreIndex.from_documents(self.documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        يسترجع سلاسل السياق الأكثر صلة بالاستعلام المحدد.
        """
        if not self.documents:
            return []

        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k * 2  # جلب المزيد لإعادة الترتيب
        )
        nodes = retriever.retrieve(query)

        # تطبيق إعادة الترتيب (هنا نعتمد على النقاط المتجهة، ولكن الهيكلية تدعم التوسع)
        reranked_nodes = self._rerank(nodes, top_k)

        return [node.get_content() for node in reranked_nodes]

    def _rerank(self, nodes: list[NodeWithScore], top_k: int) -> list[NodeWithScore]:
        """
        يعيد ترتيب العقد المسترجعة.
        حاليًا يستخدم الفرز حسب النقاط، ويمكن توسيعه باستخدام CrossEncoder.
        """
        # الفرز التنازلي حسب النقاط
        sorted_nodes = sorted(nodes, key=lambda x: x.score or 0.0, reverse=True)
        return sorted_nodes[:top_k]

def rerank_context(goal: str, context: list[str]) -> list[str]:
    """
    الواجهة العامة لإعادة ترتيب السياق بناءً على الهدف.
    """
    if not context:
        return []

    engine = ContextEngine(context)
    return engine.retrieve(goal)
