"""
Tool management endpoints.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.v2.dependencies import get_current_user_id, get_tool_registry_dependency
from app.api.v2.schemas import ToolExecutionRequest, ToolExecutionResponse
from app.core.protocols import ToolRegistryProtocol, AgentTool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    registry: ToolRegistryProtocol = Depends(get_tool_registry_dependency),
    user_id: int = Depends(get_current_user_id),
) -> ToolExecutionResponse:
    """
    Execute a tool.

    Complexity: 3
    """
    start_time = time.time()

    tool = registry.get(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")

    try:
        result = await tool.execute(**request.parameters)
        execution_time = time.time() - start_time

        return ToolExecutionResponse(
            success=True,
            result=result,
            execution_time=execution_time,
            metadata={"user_id": user_id},
        )
    except Exception as e:
        logger.error(
            f"Tool execution failed: {e}", extra={"tool": request.tool_name, "user_id": user_id}
        )
        execution_time = time.time() - start_time

        return ToolExecutionResponse(
            success=False,
            error=str(e),
            execution_time=execution_time,
            metadata={"user_id": user_id},
        )


@router.get("/list")
async def list_tools(
    category: str | None = None,
    registry: ToolRegistryProtocol = Depends(get_tool_registry_dependency),
) -> dict:
    """
    List available tools.

    Complexity: 1
    """
    tools = registry.list_tools()

    # Filter by category if requested (assuming tool has metadata, though Protocol doesn't strictly enforce 'config' attribute yet, we should use properties)
    # Since our StandardTool uses simple properties, let's adapt.
    # For now, simplistic listing.

    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in tools
        ],
        "total": len(tools),
    }

