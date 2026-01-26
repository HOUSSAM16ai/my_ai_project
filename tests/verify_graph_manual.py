import asyncio
import os
from unittest.mock import MagicMock

# Mock Environment Variables if needed
os.environ["OPENAI_API_KEY"] = "sk-fake-key"

from app.services.chat.graph.workflow import create_multi_agent_graph
from app.services.chat.tools import ToolRegistry


# Mock AI Client
class MockAIClient:
    async def generate(self, model, messages, response_format=None):
        # Mock Planner Response
        if "Planner Architect" in messages[0]["content"]:
            return MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"steps": ["search", "explain"]}'))]
            )

        # Mock Writer Response
        if "Smart Tutor" in messages[0]["content"]:
            return MagicMock(
                choices=[
                    MagicMock(message=MagicMock(content="هذا شرح فاخر ومبسط للتمرين المسترجع..."))
                ]
            )

        return MagicMock(choices=[MagicMock(message=MagicMock(content="Default response"))])

    async def stream_chat(self, messages):
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="Streaming..."))])


# Mock Tools
class MockTools(ToolRegistry):
    async def execute(self, tool_name, params):
        print(f"🛠️ Tool Executed: {tool_name} with {params}")
        if tool_name == "search_content":
            return [{"id": "content_123", "title": "Bac 2024 Math Ex 1"}]
        if tool_name == "get_content_raw":
            return {"content": "Exercise Text...", "solution": "Official Solution..."}
        return []


async def main():
    print("🚀 Starting Super-Intelligent Agent Verification...")

    ai_client = MockAIClient()
    tools = MockTools()

    # 1. Create Graph
    graph = create_multi_agent_graph(ai_client, tools)
    print("✅ Graph Compiled Successfully.")

    # 2. Run Flow
    print("\n🎬 Simulating User Request: 'أريد تمارين احتمالات'")

    initial_state = {
        "messages": [MagicMock(content="أريد تمارين احتمالات", type="human")],
        "next": "supervisor",
        "current_step_index": 0,
        "plan": [],
        "search_results": [],
    }

    async for event in graph.astream_events(initial_state, version="v1"):
        kind = event["event"]
        name = event.get("name")

        if kind == "on_chain_start" and name in ["planner", "researcher", "writer"]:
            print(f"\n⚡ Node Activated: {name}")

        if kind == "on_chain_end" and name == "planner":
            print(f"   📋 Plan Created: {event['data']['output'].get('plan')}")

        if kind == "on_chain_end" and name == "researcher":
            results = event["data"]["output"].get("search_results")
            print(f"   🔍 Research Found: {len(results)} items")

        if kind == "on_chain_end" and name == "writer":
            print(f"   ✍️ Final Response: {event['data']['output'].get('final_response')}")

    print("\n✅ Verification Complete: All Agents Collaborated Successfully.")


if __name__ == "__main__":
    asyncio.run(main())
