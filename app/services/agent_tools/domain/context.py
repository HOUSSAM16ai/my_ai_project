"""
Domain tools for context awareness (active file, line number).
"""

from app.services.agent_tools.tool_model import Tool, ToolConfig


async def context_awareness_handler(
    metadata: dict[str, object] | None = None, **kwargs
) -> dict[str, object]:
    """
    Extracts context from the incoming request metadata.
    """
    # Merge kwargs into metadata if metadata is None (legacy support)
    if metadata is None:
        metadata = kwargs

    active_file = metadata.get("active_file")
    cursor_line = metadata.get("cursor_line")
    selection = metadata.get("selection")

    if not active_file:
        return {
            "error": "No active context found. The user is not focused on a file or the client did not send context."
        }

    return {
        "active_file": active_file,
        "cursor_line": cursor_line,
        "selection": selection,
        "message": f"User is at {active_file}:{cursor_line}",
    }


class ContextAwarenessTool(Tool):
    """
    Tool to extract context from the user's active environment.
    """

    def __init__(self):
        config = ToolConfig(
            name="get_active_context",
            description="Retrieves the user's current active file, line number, and selection.",
            category="context",
            aliases=["active_file", "current_context"],
            handler=context_awareness_handler,
        )
        super().__init__(config)
