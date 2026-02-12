import httpx
from typing import List, Any, Dict, Optional
from app.core.interfaces.services import IResearchService
from app.domain.models.agents import SearchRequest, SearchResult
from app.core.logging import get_logger

logger = get_logger(__name__)

class HttpResearchClient(IResearchService):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        try:
            payload = {
                "caller_id": "app-core",
                "action": "search",
                "payload": request.model_dump(exclude_none=True)
            }
            # The agent expects filters inside 'payload' to be a dict, but SearchRequest puts them there.
            # Let's adjust payload matching the agent's expectation:
            # Agent expects: query, filters, limit.

            # Re-mapping to agent's flat payload structure if needed, or nested?
            # Agent code: query = request.payload.get("query")
            #             filters_dict = request.payload.get("filters")

            # SearchRequest has 'q' not 'query'. Map it.
            actual_payload = {
                "query": request.q,
                "filters": request.filters.model_dump(exclude_none=True),
                "limit": request.limit
            }

            response = await self.client.post("/execute", json={
                "caller_id": "app-core",
                "target_service": "research_agent",
                "action": "search",
                "payload": actual_payload
            })
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                logger.error(f"Research Agent Error: {data.get('error')}")
                return []

            results_data = data.get("data", {}).get("results", [])
            return [SearchResult(**r) for r in results_data]

        except Exception as e:
            logger.error(f"Failed to call Research Agent: {e}")
            raise

    async def refine_query(self, query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        try:
            payload = {
                "query": query,
                "api_key": api_key
            }
            response = await self.client.post("/execute", json={
                "caller_id": "app-core",
                "target_service": "research_agent",
                "action": "refine",
                "payload": payload
            })
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise RuntimeError(data.get("error"))

            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to refine query: {e}")
            raise

    async def deep_research(self, query: str) -> str:
        try:
            payload = {
                "query": query,
                "deep_dive": True
            }
            response = await self.client.post("/execute", json={
                "caller_id": "app-core",
                "target_service": "research_agent",
                "action": "deep_research",
                "payload": payload
            })
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise RuntimeError(data.get("error"))

            # Agent wraps result in a list of results with 'content'
            results = data.get("data", {}).get("results", [])
            if results:
                return results[0].get("content", "")
            return ""
        except Exception as e:
            logger.error(f"Failed to perform deep research: {e}")
            raise

    async def close(self):
        await self.client.aclose()
