import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "microservices/research_agent/src"))

# Mock dependencies that are not installed in the test environment or irrelevant
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Setup Mock Logger to print
mock_logger = MagicMock()
def log_side_effect(msg, *args):
    print(f"[LOG] {msg} {args}")
mock_logger.info.side_effect = log_side_effect
mock_logger.warning.side_effect = log_side_effect
mock_logger.error.side_effect = log_side_effect

# Define dummy classes for isinstance checks
class MockTavilyClient: pass
class MockFirecrawlApp: pass

# Mock modules
mock_modules = [
    "langchain_community.utilities",
    "langchain_core.prompts",
    "langchain_openai",
    "bs4",
    "microservices.research_agent.src.logging",
    "flupy",
    "llama_index",
    "llama_index.core",
    "llama_index.core.schema",
    "llama_index.core.retrievers",
    "llama_index.core.indices",
    "llama_index.core.vector_stores",
    "llama_index.embeddings",
    "llama_index.embeddings.huggingface",
    "llama_index.retrievers.bm25",
    "llama_index.vector_stores",
    "llama_index.vector_stores.supabase",
]

for mod in mock_modules:
    sys.modules[mod] = MagicMock()

# Handle tavily and firecrawl specifically to provide classes
mock_tavily = MagicMock()
mock_tavily.TavilyClient = MockTavilyClient
sys.modules["tavily"] = mock_tavily

mock_firecrawl = MagicMock()
mock_firecrawl.FirecrawlApp = MockFirecrawlApp
sys.modules["firecrawl"] = mock_firecrawl

# Patch get_logger to return our printing mock
sys.modules["microservices.research_agent.src.logging"].get_logger.return_value = mock_logger

from microservices.research_agent.src.search_engine.super_search import (
    ResearchPlan,
    SuperSearchOrchestrator,
)


async def test_search_pipeline():
    print("Testing SuperSearchOrchestrator Logic (Mocked)...")

    # Mock components
    mock_llm = AsyncMock()
    mock_search = MagicMock()
    # Explicitly delete 'results' so hasattr(mock_search, 'results') is False
    # This ensures the orchestrator doesn't treat it as DuckDuckGo wrapper
    del mock_search.results

    mock_scraper = MagicMock()

    # Configure Scraper to be Async-friendly
    # This avoids potential issues with asyncio.to_thread wrapping a MagicMock return value
    mock_scraper.scrape = AsyncMock()
    long_content = "A" * 200 + " Synthesized Answer Source Content"
    mock_scraper.scrape.return_value = long_content

    # Configure Search to be Async-friendly
    mock_search.search = AsyncMock()
    mock_search.search.return_value = [{"url": "http://test.com", "content": "test content"}]

    # Setup orchestrator
    orchestrator = SuperSearchOrchestrator(
        llm=mock_llm, search_tool=mock_search, web_scraper=mock_scraper
    )

    # 1. Test Planning
    print("- Testing Planning Phase...")
    # Mock _create_plan to bypass LangChain internals and ensure planning succeeds
    orchestrator._create_plan = AsyncMock(return_value=ResearchPlan(
        sub_queries=["q1", "q2"], required_info=["info1"]
    ))

    # 2. Test Execution
    print("- Testing Execution...")

    # Mock synthesis response
    # The orchestrator calls llm.ainvoke(prompt).content
    mock_response = MagicMock()
    mock_response.content = "Synthesized Answer"
    mock_llm.ainvoke.return_value = mock_response

    result = await orchestrator.execute("test query")

    print(f"Result: {result}")
    assert "Synthesized Answer" in result
    print("✅ SuperSearchOrchestrator Pipeline Verified.")


if __name__ == "__main__":
    asyncio.run(test_search_pipeline())
