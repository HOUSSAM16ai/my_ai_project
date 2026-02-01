import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock heavy dependencies
sys.modules["app.services.overmind.langgraph"] = MagicMock()
sys.modules["microservices.research_agent.src.search_engine"] = MagicMock()
sys.modules["microservices.planning_agent.cognitive"] = MagicMock()
# llama_index.core is installed

sys.modules["app.services.chat.agents.data_access"] = MagicMock()
sys.modules["app.services.chat.agents.refactor"] = MagicMock()

sys.modules["app.services.chat.agents.admin_handlers.base"] = MagicMock()
sys.modules["app.services.chat.agents.admin_handlers.code"] = MagicMock()
sys.modules["app.services.chat.agents.admin_handlers.database"] = MagicMock()
sys.modules["app.services.chat.agents.admin_handlers.project"] = MagicMock()
sys.modules["app.services.chat.agents.admin_handlers.users"] = MagicMock()

sys.modules["langgraph.graph"] = MagicMock()
sys.modules["langgraph.prebuilt"] = MagicMock()

sys.modules["app.services.chat.graph.search"] = MagicMock()

from app.services.chat.agents.admin import AdminAgent
from app.services.chat.graph.nodes.researcher import researcher_node
from app.services.chat.tools import ToolRegistry


class TestFullStackFlow(unittest.IsolatedAsyncioTestCase):
    async def test_admin_flow_uses_mcp(self):
        """
        Verify that AdminAgent uses MCPIntegrations for complex tasks.
        """
        # Setup
        tools = ToolRegistry()
        ai_client = MagicMock()  # Changed from AsyncMock to MagicMock

        # Mock AI Client to return specific triggers
        # stream_chat should return an async iterator
        ai_client.stream_chat.return_value = self._mock_stream("EXECUTE_TOOL: complex_reasoning")

        agent = AdminAgent(tools, ai_client)
        # Clear handlers to force fallback to dynamic router (Step 2)
        agent.handlers = []

        # Mock MCP
        agent.mcp = AsyncMock()
        agent.mcp.run_langgraph_workflow.return_value = {
            "success": True,
            "final_answer": "Reasoned Answer",
        }
        agent.mcp.semantic_search.return_value = {"success": True, "results": []}

        # Test Complex Reasoning
        print("\n--- Testing Admin Complex Reasoning ---")
        responses = []
        async for resp in agent.run("Analyze the architectural implications of X"):
            responses.append(resp)

        # Verify call
        agent.mcp.run_langgraph_workflow.assert_called_once()
        self.assertIn("النتيجة النهائية", "".join(responses))

        # 2. Deep Research
        # Reset mocks
        ai_client.stream_chat.return_value = self._mock_stream("EXECUTE_TOOL: deep_research")
        agent.mcp.reset_mock()

        print("\n--- Testing Admin Deep Research ---")
        async for _resp in agent.run("Find academic papers about Y"):
            pass

        # Verify call
        agent.mcp.semantic_search.assert_called_once()

    async def test_student_flow_uses_kagent(self):
        """
        Verify that Student Researcher uses Kagent.
        """
        kagent_mesh = AsyncMock()
        kagent_mesh.execute_action.return_value.status = "success"
        kagent_mesh.execute_action.return_value.data = {"results": ["Doc 1"]}

        state = {"messages": [MagicMock(content="Search for X")], "current_step_index": 0}

        print("\n--- Testing Student Researcher Flow ---")
        with patch("app.services.chat.graph.nodes.researcher.build_graph_search_plan") as mock_plan:
            mock_plan.return_value.queries = ["Search for X"]
            await researcher_node(state, kagent_mesh)

        kagent_mesh.execute_action.assert_called_once()
        args = kagent_mesh.execute_action.call_args[0][0]
        self.assertEqual(args.target_service, "research_agent")
        self.assertEqual(args.action, "search")
        print("Student flow correctly delegated to 'research_agent' via Kagent.")

    async def _mock_stream(self, content):
        """Helper to mock stream_chat generator."""
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = content
        yield chunk


if __name__ == "__main__":
    unittest.main()
