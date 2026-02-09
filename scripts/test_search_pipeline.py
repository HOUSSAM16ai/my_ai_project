
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(os.getcwd())

# Define Mock Classes to satisfy isinstance checks
class MockTavilyClient:
    def __init__(self, api_key=None): pass
    def search(self, *args, **kwargs): pass

class MockFirecrawlApp:
    def __init__(self, api_key=None): pass
    def scrape_url(self, *args, **kwargs): pass

# Mock modules
mock_tavily_module = MagicMock()
mock_tavily_module.TavilyClient = MockTavilyClient
sys.modules['tavily'] = mock_tavily_module

mock_firecrawl_module = MagicMock()
mock_firecrawl_module.FirecrawlApp = MockFirecrawlApp
sys.modules['firecrawl'] = mock_firecrawl_module

# Mock all llama_index related modules
sys.modules['llama_index'] = MagicMock()
sys.modules['llama_index.core'] = MagicMock()
sys.modules['llama_index.core.schema'] = MagicMock()
sys.modules['llama_index.core.vector_stores'] = MagicMock()
sys.modules['llama_index.embeddings'] = MagicMock()
sys.modules['llama_index.embeddings.huggingface'] = MagicMock()
sys.modules['llama_index.vector_stores'] = MagicMock()
sys.modules['llama_index.vector_stores.supabase'] = MagicMock()
sys.modules['vecs'] = MagicMock()
sys.modules['flupy'] = MagicMock()

from microservices.research_agent.src.search_engine.super_search import (
    SuperSearchOrchestrator,
    ResearchPlan,
    SearchResult
)

async def test_search_pipeline():
    print("Testing SuperSearchOrchestrator Pipeline...")

    # Mock LLM
    mock_llm = AsyncMock()

    # Mock structured output for Planning Phase
    mock_runnable = AsyncMock()
    mock_runnable.ainvoke.return_value = ResearchPlan(
        sub_queries=["query 1", "query 2"],
        required_info=["fact 1", "fact 2"]
    )

    # Mock LLM for Synthesis and Deep Dive
    mock_llm.ainvoke.return_value = MagicMock(content="Synthesized Answer based on context.")

    # Mock Search Tool (Tavily)
    mock_search_tool = MockTavilyClient()
    mock_search_tool.search = MagicMock(return_value={"results": [{"url": "http://test.com", "content": "Test content"}]})

    # Mock Scraper (Firecrawl)
    mock_scraper = MockFirecrawlApp()
    # Content must be > 100 chars
    long_content = "Deep content from test.com " * 10
    mock_scraper.scrape_url = MagicMock(return_value={"markdown": long_content})

    # Instantiate Orchestrator with mocks
    orchestrator = SuperSearchOrchestrator(
        llm=mock_llm,
        search_tool=mock_search_tool,
        web_scraper=mock_scraper
    )

    # Patch _create_plan
    orchestrator._create_plan = AsyncMock(return_value=ResearchPlan(
        sub_queries=["sub query 1"],
        required_info=["info 1"]
    ))

    # Execute
    query = "Test Query"
    result = await orchestrator.execute(query)

    print(f"Result: {result}")

    # Assertions
    assert "Synthesized Answer" in result
    print("Assertion Passed: Result contains synthesized answer.")

    orchestrator._create_plan.assert_called_once()
    print("Assertion Passed: Planning phase executed.")

    mock_search_tool.search.assert_called()
    print("Assertion Passed: Search phase executed (Tavily).")

    mock_scraper.scrape_url.assert_called()
    print("Assertion Passed: Deep Ingestion phase executed (Firecrawl).")

    print("Pipeline Test Successful!")

if __name__ == "__main__":
    asyncio.run(test_search_pipeline())
