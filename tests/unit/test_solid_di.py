import asyncio
import sys
from unittest.mock import MagicMock

# --- MOCKING HEAVY DEPENDENCIES BEFORE IMPORTS ---

# Mock external heavy dependencies
mock_llama = MagicMock()


# Create a dummy Workflow class to avoid MagicMock inheritance issues
class MockWorkflow:
    def __init__(self, *args, **kwargs):
        pass


# We need to set Workflow on the mock module
mock_llama_workflow = MagicMock()
mock_llama_workflow.Workflow = MockWorkflow
mock_llama_workflow.Context = MagicMock()
mock_llama_workflow.Event = MagicMock()
mock_llama_workflow.StartEvent = MagicMock()
mock_llama_workflow.StopEvent = MagicMock()
# step decorator needs to be a function returning the function
mock_llama_workflow.step = lambda x: x

sys.modules["llama_index"] = mock_llama
sys.modules["llama_index.core"] = mock_llama
sys.modules["llama_index.core.schema"] = mock_llama
sys.modules["llama_index.core.workflow"] = mock_llama_workflow  # Use specific mock
sys.modules["llama_index.core.retrievers"] = mock_llama
sys.modules["llama_index.core.vector_stores"] = mock_llama
sys.modules["llama_index.embeddings"] = mock_llama
sys.modules["llama_index.embeddings.huggingface"] = mock_llama
sys.modules["llama_index.vector_stores"] = mock_llama
sys.modules["llama_index.vector_stores.supabase"] = mock_llama

# Mock sqlalchemy
mock_sa = MagicMock()
mock_sa.Column = MagicMock()
# Setup make_url to return a mock with drivername
mock_url = MagicMock()
mock_url.drivername = "postgresql+asyncpg"
mock_sa.engine.url.make_url.return_value = mock_url

sys.modules["sqlalchemy"] = mock_sa
sys.modules["sqlalchemy.orm"] = mock_sa
sys.modules["sqlalchemy.ext"] = mock_sa
sys.modules["sqlalchemy.ext.asyncio"] = mock_sa
sys.modules["sqlalchemy.engine"] = mock_sa
sys.modules["sqlalchemy.engine.interfaces"] = mock_sa
sys.modules["sqlalchemy.engine.url"] = mock_sa
sys.modules["sqlalchemy.types"] = mock_sa
sys.modules["sqlalchemy.dialects"] = mock_sa
sys.modules["sqlalchemy.dialects.postgresql"] = mock_sa

# Mock sqlmodel
mock_sqlmodel = MagicMock()
sys.modules["sqlmodel"] = mock_sqlmodel

# Mock yaml
sys.modules["yaml"] = MagicMock()

# Mock pydantic
mock_pydantic = MagicMock()
sys.modules["pydantic"] = mock_pydantic
sys.modules["pydantic_settings"] = MagicMock()

# Mock settings
mock_settings_module = MagicMock()
mock_settings_obj = MagicMock()
mock_settings_obj.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
mock_settings_obj.DEBUG = True
mock_settings_obj.ENVIRONMENT = "development"
mock_settings_obj.SERVICE_NAME = "test-service"
mock_settings_module.get_settings.return_value = mock_settings_obj

sys.modules["app.core.settings.base"] = mock_settings_module
sys.modules["app.core.config"] = mock_settings_module  # Alias it

# Mock httpx
sys.modules["httpx"] = MagicMock()

# Mock pythonjsonlogger
sys.modules["pythonjsonlogger"] = MagicMock()
sys.modules["pythonjsonlogger.jsonlogger"] = MagicMock()

# Mock langchain_core
mock_lc = MagicMock()
sys.modules["langchain_core"] = mock_lc
sys.modules["langchain_core.messages"] = mock_lc

# Mock dspy
sys.modules["dspy"] = MagicMock()

# Mock fastapi
sys.modules["fastapi"] = MagicMock()
sys.modules["passlib"] = MagicMock()
sys.modules["passlib.context"] = MagicMock()

# Mock sentence_transformers
sys.modules["sentence_transformers"] = MagicMock()

# Mock the troublesome mission domain to avoid SQLModel definition errors
sys.modules["app.core.domain.mission"] = MagicMock()
sys.modules["app.core.domain.chat"] = MagicMock()

# Mock models that use pydantic heavily and cause typing issues with mocks
sys.modules["app.services.reasoning.models"] = MagicMock()

# Mock retriever module to avoid metaclass conflict between Mock and ABC
sys.modules["app.services.search_engine.llama_retriever"] = MagicMock()

# --- END MOCKS ---

from app.core.di import Container

# Re-import interfaces now that models are mocked
from app.core.interfaces import (
    IContextComposer,
    IIntentDetector,
    IPromptStrategist,
    IReasoningStrategy,
)
from app.services.chat.graph.domain import WriterIntent

# We need to re-import writer node AFTER mocking
from app.services.chat.graph.nodes.writer import writer_node
from app.services.reasoning.workflow import SuperReasoningWorkflow

# Mock AIMessage since we mocked the module
AIMessage = MagicMock()


async def verify_writer_di():
    print("Verifying WriterNode DI...")

    # Mock dependencies
    mock_detector = MagicMock(spec=IIntentDetector)
    mock_detector.analyze.return_value = WriterIntent.GENERAL_INQUIRY

    mock_composer = MagicMock(spec=IContextComposer)
    mock_composer.compose.return_value = "Mock Context"

    mock_strategist = MagicMock(spec=IPromptStrategist)
    mock_strategist.build_prompt.return_value = "Mock System Prompt"

    # Register Mocks (Overwriting the defaults registered in the module)
    Container.register_singleton(IIntentDetector, mock_detector)
    Container.register_singleton(IContextComposer, mock_composer)
    Container.register_singleton(IPromptStrategist, mock_strategist)

    # Mock State and Client
    msg = MagicMock()
    msg.content = "Hello"

    mock_state = {
        "messages": [msg],
        "current_step_index": 0,
        "search_results": [],
        "diagnosis": "Average",
        "review_feedback": None,
    }

    mock_client = MagicMock()
    # Mocking the async send_message
    f = asyncio.Future()
    f.set_result("AI Response")
    mock_client.send_message.return_value = f

    # Run Node
    result = await writer_node(mock_state, mock_client)

    # Check result content - since AIMessage is mocked, result["messages"][0] is a mock
    # But final_response is a string "AI Response"
    assert result["final_response"] == "AI Response"

    mock_detector.analyze.assert_called_once()
    mock_composer.compose.assert_called_once()
    mock_strategist.build_prompt.assert_called_once()
    print("WriterNode DI Verified!")


def verify_workflow_di():
    print("Verifying Workflow DI...")
    mock_client = MagicMock()
    mock_retriever = MagicMock()
    mock_strategy = MagicMock(spec=IReasoningStrategy)

    wf = SuperReasoningWorkflow(
        client=mock_client, retriever=mock_retriever, strategy=mock_strategy
    )

    print(f"wf.retriever: {wf.retriever}")
    print(f"mock_retriever: {mock_retriever}")

    assert wf.retriever == mock_retriever
    assert wf.strategy == mock_strategy
    print("Workflow DI Verified!")


async def main():
    await verify_writer_di()
    verify_workflow_di()


if __name__ == "__main__":
    asyncio.run(main())
