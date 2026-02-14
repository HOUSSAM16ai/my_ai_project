"""
عميل استرجاع المعرفة عن بعد (Remote Retriever).
---------------------------------------------
يقوم هذا الفصل بالاتصال بوكيل البحث (Research Agent) عبر واجهة برمجة التطبيقات (API)
بدلاً من استيراد الكود مباشرة، مما يحقق الفصل التام بين الخدمات.
"""

import os

import httpx

from microservices.reasoning_agent.src.compat import NodeWithScore, TextNode
from microservices.reasoning_agent.src.interfaces import IKnowledgeRetriever
from microservices.reasoning_agent.src.logging import get_logger

logger = get_logger("remote-retriever")


class RemoteKnowledgeGraphRetriever(IKnowledgeRetriever):
    """
    مسترجع يستخدم API وكيل البحث للوصول إلى الرسم البياني للمعرفة.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.base_url = os.getenv("RESEARCH_AGENT_URL", "http://research-agent:8000")
        self.timeout = 30.0

    async def aretrieve(self, query: str) -> list[NodeWithScore]:
        """
        يرسل طلب استرجاع إلى وكيل البحث ويعيد النتائج كقائمة من العقد.
        """
        logger.info(f"Retrieving from Research Agent ({self.base_url}): {query}")

        payload = {
            "caller_id": "reasoning-agent",
            "action": "retrieve_knowledge_graph",
            "payload": {"query": query, "limit": self.top_k},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/execute", json=payload)
                response.raise_for_status()
                resp_data = response.json()

            if resp_data.get("status") != "success":
                logger.error(f"Research Agent returned error: {resp_data.get('error')}")
                return []

            raw_nodes = resp_data.get("data", [])
            nodes = []

            for item in raw_nodes:
                text = item.get("text", "")
                metadata = item.get("metadata", {})
                score = item.get("score", 0.0)

                # Create TextNode first
                try:
                    # Try keyword arguments first (safe for both mock and typical Pydantic/LlamaIndex)
                    node = TextNode(text=text, metadata=metadata)
                except TypeError:
                    # Fallback if signature is different (unlikely but safe)
                    node = TextNode()
                    node.text = text
                    node.metadata = metadata

                # Create NodeWithScore
                nws = NodeWithScore(node=node, score=score)
                nodes.append(nws)

            return nodes

        except Exception as e:
            logger.error(f"Remote retrieval failed: {e}")
            return []
