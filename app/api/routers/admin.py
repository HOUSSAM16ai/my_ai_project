# app/api/routers/admin.py
"""
Admin-facing API endpoints for the CogniForge platform.
This includes routes for the admin dashboard, chat functionality,
and other administrative tasks.
"""
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.factories import get_ai_gateway
from app.gateways.ai_service_gateway import AIServiceGateway

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serves the admin dashboard page."""
    # In a real app, you'd pass user data from the request context.
    # For now, we pass a placeholder.
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "current_user": {"full_name": "Admin"}}
    )


@router.post("/api/chat/stream", summary="Admin Chat Streaming Endpoint")
async def chat_stream(
    request: Request,
    gateway: AIServiceGateway = Depends(get_ai_gateway),
):
    """
    Handles POST requests to initiate a chat stream.
    Processes the incoming question and streams back the response chunk by chunk,
    using a dependency-injected AI Service Gateway.
    """
    try:
        body = await request.json()
        question = body.get("question", "")
        if not question or not question.strip():

            async def error_stream():
                error_payload = {"type": "error", "payload": {"error": "Question is required."}}
                yield f"data: {json.dumps(error_payload)}\\n\\n"

            return StreamingResponse(error_stream(), media_type="text/event-stream")
    except json.JSONDecodeError:

        async def error_stream():
            error_payload = {"type": "error", "payload": {"error": "Invalid JSON payload."}}
            yield f"data: {json.dumps(error_payload)}\\n\\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def response_generator():
        try:
            # In a real app, user_id and conversation_id would come from the session or request context.
            user_id = "admin_user_http_stream"  # Placeholder
            conversation_id = body.get("conversation_id")
            for chunk in gateway.stream_chat(question, conversation_id, user_id):
                yield f"data: {json.dumps(chunk)}\\n\\n"
        except Exception as e:
            error_payload = {
                "type": "error",
                "payload": {"error": f"Failed to connect to AI service: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\\n\\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")
