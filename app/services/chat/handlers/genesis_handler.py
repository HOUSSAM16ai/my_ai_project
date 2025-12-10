"""
Genesis Handler for Chat Orchestrator.
Adapts the powerful GenesisAgent to the Orchestrator stream protocol.
"""
from typing import AsyncGenerator
# Local import inside function to avoid circular dependency
from app.genesis.tools.code_explorer import grep_code, read_file_segment, list_files, identify_hotspots

async def handle_genesis_analysis(
    question: str,
    user_id: int
) -> AsyncGenerator[str, None]:
    """
    Delegates complex analysis to Genesis Agent.
    """
    yield "🔎 **Genesis Analysis Started**\n"
    yield f"🧠 Thinking about: *{question}*\n\n"

    try:
        from app.genesis.core import GenesisAgent  # Moved import here

        # Initialize Genesis with Tools
        agent = GenesisAgent(model="gpt-4o")
        agent.register_tool(grep_code)
        agent.register_tool(read_file_segment)
        agent.register_tool(list_files)
        agent.register_tool(identify_hotspots)

        # Capture the answer
        result = agent.run(question)

        yield result

    except Exception as e:
        yield f"❌ **Genesis Error:** {str(e)}"
