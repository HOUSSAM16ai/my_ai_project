import re

from llama_index.core.schema import NodeWithScore
from sentence_transformers import CrossEncoder

from app.core.logging import get_logger

logger = get_logger(__name__)

# Singleton instance
_RERANKER_INSTANCE = None


class Reranker:
    """
    محرك إعادة الترتيب (Reranker) لتحسين نتائج البحث الدلالي.
    يستخدم نموذج Cross-Encoder لإعادة تقييم الصلة بين الاستعلام والوثائق المسترجعة.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        try:
            # We trust the environment to have the model cached or download it.
            self.model = CrossEncoder(model_name)
            logger.info(f"Reranker model {model_name} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Reranker model {model_name}: {e}")
            self.model = None

    def rerank(self, query: str, nodes: list[NodeWithScore], top_n: int = 5) -> list[NodeWithScore]:
        """
        إعادة ترتيب قائمة الوثائق بناءً على صلتها بالاستعلام.
        يدعم التحسين القائم على الحبيبات (Granularity Boosting).
        """
        if not nodes:
            return []

        if not self.model:
            return nodes[:top_n]

        try:
            # 1. Semantic Scoring via Cross-Encoder
            doc_texts = [n.node.get_content() for n in nodes]
            pairs = [[query, doc_text] for doc_text in doc_texts]
            scores = self.model.predict(pairs)

            # 2. Granularity Boosting
            # If the user asks for "Part 1", and a chunk explicitly mentions "Part 1", boost it.
            granularity_pattern = self._extract_granularity_pattern(query)

            for i, node in enumerate(nodes):
                base_score = float(scores[i])

                # Apply Boost
                if granularity_pattern:
                    content = node.node.get_content()
                    if re.search(granularity_pattern, content, re.IGNORECASE):
                        # Boost significantly (e.g. +2.0 logits) to prioritize exact part matches
                        base_score += 2.0

                node.score = base_score

            # Sort by new score descending
            nodes.sort(key=lambda x: x.score if x.score is not None else -1.0, reverse=True)

            return nodes[:top_n]

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original order
            return nodes[:top_n]

    def _extract_granularity_pattern(self, query: str) -> str | None:
        """
        Constructs a regex pattern to match requested granularity in the text.
        e.g. "Question 1" -> r"(Question|Exercise|السؤال|التمرين)\s*1"
        """
        # Arabic/English keywords
        q_keywords = r"(Question|Exercise|السؤال|التمرين)"
        p_keywords = r"(Part|Section|الجزء)"

        # Match "Question X"
        q_match = re.search(rf"{q_keywords}\s*(?:No\.?|رقم)?\s*(\d+|[٠-٩]+|One|Two|Three|الأول|الثاني)", query, re.IGNORECASE)
        if q_match:
             # Create a loose match for the content
             num = q_match.group(2)
             return rf"{q_keywords}\s*(?:No\.?|رقم)?\s*{re.escape(num)}"

        # Match "Part X"
        p_match = re.search(rf"{p_keywords}\s*(?:No\.?|رقم)?\s*(\d+|[٠-٩]+|One|Two|Three|الأول|الثاني)", query, re.IGNORECASE)
        if p_match:
             num = p_match.group(2)
             return rf"{p_keywords}\s*(?:No\.?|رقم)?\s*{re.escape(num)}"

        return None


def get_reranker() -> Reranker:
    global _RERANKER_INSTANCE
    if _RERANKER_INSTANCE is None:
        _RERANKER_INSTANCE = Reranker()
    return _RERANKER_INSTANCE
