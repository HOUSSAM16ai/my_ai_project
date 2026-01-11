import pytest

from app.services.chat.agents.orchestrator import OrchestratorAgent


class FakeTools:
    def __init__(self, responses: dict[str, object]) -> None:
        self._responses = responses

    async def execute(self, tool_name: str, args: dict[str, object]) -> object:
        return self._responses[tool_name]


class FakeAgent:
    def __init__(self, success: bool = True, message: str = "ok") -> None:
        self._success = success
        self._message = message

    async def process(self, _: dict[str, object]):
        return type("Response", (), {"success": self._success, "message": self._message})()


@pytest.mark.asyncio
async def test_orchestrator_agent_user_count() -> None:
    tools = FakeTools({"get_user_count": 7})
    agent = OrchestratorAgent(ai_client=None, tools=tools)  # type: ignore[arg-type]
    agent.data_agent = FakeAgent()

    response = await agent.run("كم عدد المستخدمين؟")

    assert "7" in response


@pytest.mark.asyncio
async def test_orchestrator_agent_table_schema() -> None:
    tools = FakeTools(
        {
            "get_table_schema": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "email", "type": "VARCHAR"},
                ]
            }
        }
    )
    agent = OrchestratorAgent(ai_client=None, tools=tools)  # type: ignore[arg-type]

    response = await agent.run("اعرض مخطط جدول users")

    assert "users" in response
    assert "id" in response
    assert "email" in response


@pytest.mark.asyncio
async def test_orchestrator_agent_code_search() -> None:
    tools = FakeTools(
        {
            "search_codebase": [
                {
                    "file_path": "app/services/chat/orchestrator.py",
                    "line_number": 42,
                    "match_context": "class ChatOrchestrator",
                }
            ]
        }
    )
    agent = OrchestratorAgent(ai_client=None, tools=tools)  # type: ignore[arg-type]
    agent.refactor_agent = FakeAgent()

    response = await agent.run("أين يوجد ChatOrchestrator؟")

    assert "ChatOrchestrator" in response
    assert "app/services/chat/orchestrator.py" in response


@pytest.mark.asyncio
async def test_orchestrator_agent_file_snippet() -> None:
    tools = FakeTools(
        {
            "read_file_snippet": {
                "file_path": "app/services/chat/orchestrator.py",
                "start_line": 120,
                "end_line": 121,
                "lines": ["class ChatOrchestrator:", "    pass"],
            }
        }
    )
    agent = OrchestratorAgent(ai_client=None, tools=tools)  # type: ignore[arg-type]

    response = await agent.run("اعرض app/services/chat/orchestrator.py:120")

    assert "app/services/chat/orchestrator.py" in response
    assert "120" in response
    assert "class ChatOrchestrator" in response


@pytest.mark.asyncio
async def test_orchestrator_agent_database_map() -> None:
    tools = FakeTools(
        {
            "get_database_map": {
                "tables": ["users", "admin_messages"],
                "relationships": [
                    {
                        "from_table": "admin_messages",
                        "to_table": "admin_conversations",
                        "from_column": "conversation_id",
                        "to_column": "id",
                    }
                ],
            }
        }
    )
    agent = OrchestratorAgent(ai_client=None, tools=tools)  # type: ignore[arg-type]

    response = await agent.run("أريد خريطة قاعدة البيانات والعلاقات")

    assert "خريطة قاعدة البيانات" in response
    assert "admin_messages" in response
