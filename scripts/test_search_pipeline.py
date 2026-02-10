import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "microservices/research_agent/src"))

# Mock dependencies that are not installed in the test environment or irrelevant
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that might not be importable in the CI environment
sys.path.append(os.path.join(os.getcwd(), "microservices/research_agent/src"))

# Mock unnecessary imports for this specific test
sys.modules['langchain_community.utilities'] = MagicMock()
sys.modules['langchain_core.prompts'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['tavily'] = MagicMock()
sys.modules['firecrawl'] = MagicMock()
sys.modules['microservices.research_agent.src.logging'] = MagicMock()
sys.modules['flupy'] = MagicMock()

from microservices.research_agent.src.search_engine.super_search import (
    ResearchPlan,
    SuperSearchOrchestrator,
)


async def test_search_pipeline():
    print("Testing SuperSearchOrchestrator Logic (Mocked)...")

    # Mock components
    mock_llm = AsyncMock()
    mock_search = MagicMock()
    mock_scraper = MagicMock()

    # Setup orchestrator
    orchestrator = SuperSearchOrchestrator(
        llm=mock_llm,
        search_tool=mock_search,
        web_scraper=mock_scraper
    )

    # 1. Test Planning
    print("- Testing Planning Phase...")
    mock_llm.with_structured_output.return_value.ainvoke.return_value = ResearchPlan(
        sub_queries=["q1", "q2"],
        required_info=["info1"]
    )

    # 2. Test Execution
    print("- Testing Execution...")
    # Mock search results
    mock_search.search.return_value = [{"url": "http://test.com", "content": "test content"}]

    # Mock deep dive
    mock_scraper.scrape_url.return_value = {"markdown": "Full page content"}
    mock_llm.ainvoke.return_value.content = "Synthesized Answer"

    result = await orchestrator.execute("test query")

    assert "Synthesized Answer" in result
    print("✅ SuperSearchOrchestrator Pipeline Verified.")

if __name__ == "__main__":
    asyncio.run(test_search_pipeline())
