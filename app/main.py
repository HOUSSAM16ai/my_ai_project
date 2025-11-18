# app/main.py
import asyncio
import json
import os
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.gateways.ai_service_gateway import get_ai_service_gateway

app = FastAPI(title="CogniForge - Unified ASGI Service")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health", summary="Health Check Endpoint", tags=["System"])
async def health():
    """
    Returns a 200 OK status if the service is up and running.
    Used by the healthcheck in docker-compose to verify service readiness.
    """
    return JSONResponse(content={"status": "ok", "timestamp": time.time()})


async def sse_keepalive() -> AsyncIterator[str]:
    """A simple SSE generator that sends a keepalive ping every 15 seconds."""
    while True:
        yield "event: keepalive\ndata: \n\n"
        await asyncio.sleep(15)


@app.get("/sse", summary="General Server-Sent Events Endpoint", tags=["Streaming"])
async def sse():
    """Provides a continuous stream of keepalive events."""
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
    }
    return StreamingResponse(sse_keepalive(), headers=headers)


@app.post(
    "/admin/api/chat/stream", summary="Admin Chat Streaming Endpoint", tags=["Admin", "Streaming"]
)
async def chat_stream(request: Request):
    """
    Handles POST requests to initiate a chat stream.
    Processes the incoming question and streams back the response chunk by chunk.
    """
    try:
        body = await request.json()
        question = body.get("question", "")
        if not question or not question.strip():

            async def error_stream():
                error_payload = {"type": "error", "payload": {"error": "Question is required."}}
                yield f"data: {json.dumps(error_payload)}\n\n"

            return StreamingResponse(error_stream(), media_type="text/event-stream")
    except Exception:

        async def error_stream():
            error_payload = {"type": "error", "payload": {"error": "Invalid JSON payload."}}
            yield f"data: {json.dumps(error_payload)}\n\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    gateway = get_ai_service_gateway()
    if not gateway:

        async def error_stream():
            error_payload = {
                "type": "error",
                "payload": {"error": "AI service is currently unavailable."},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def response_generator():
        try:
            # In a real app, you'd get the user_id and conversation_id from the session or request context
            user_id = "admin_user_http_stream"  # Placeholder
            conversation_id = body.get("conversation_id")
            for chunk in gateway.stream_chat(question, conversation_id, user_id):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            error_payload = {
                "type": "error",
                "payload": {"error": f"Failed to connect to AI service: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")


# The root endpoint can provide basic information or API documentation link
@app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    return {"message": "Welcome to the CogniForge ASGI service. See /docs for API documentation."}


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serves the admin dashboard page."""
    # In a real app, you'd pass user data. For now, we pass a placeholder.
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "current_user": {"full_name": "Admin"}}
    )


# --- AI Service Configuration ---
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai_service_standalone:8000")
SECRET_KEY = os.environ.get("SECRET_KEY", "a-super-secret-key-that-you-should-change")


def _generate_service_token(user_id: str) -> str:
    """Generates a short-lived JWT for authenticating with the AI service."""
    payload = {
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "iat": datetime.now(UTC),
        "sub": user_id,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    The main WebSocket endpoint for the admin chat.
    Handles the connection, receives messages, and streams back AI responses.
    """
    await websocket.accept()
    # Note: In a real application, you'd get the user_id from the WebSocket's
    # authentication context (e.g., a token passed on connection).
    # For this implementation, we'll hardcode it as we don't have user sessions
    # in this standalone service.
    user_id = "admin_user_websocket"

    try:
        while True:
            question = await websocket.receive_text()

            service_token = _generate_service_token(user_id)
            headers = {
                "Authorization": f"Bearer {service_token}",
                "Content-Type": "application/json",
            }
            payload = {"question": question, "conversation_id": None}
            stream_url = f"{AI_SERVICE_URL}/api/v1/chat/stream"

            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST", stream_url, headers=headers, json=payload
                    ) as response:
                        # Check for successful response
                        if response.status_code != 200:
                            error_body = await response.aread()
                            await websocket.send_text(
                                f"Error: Failed to connect to AI service. Status: {response.status_code}, Body: {error_body.decode()}"
                            )
                            continue

                        # Stream the response back to the client
                        async for line in response.aiter_lines():
                            if line:
                                # Send the raw chunk to the client, let the frontend parse it
                                await websocket.send_text(line)

            except httpx.RequestError as e:
                await websocket.send_text(f"Error: Could not connect to the AI service: {e}")
            except Exception as e:
                await websocket.send_text(
                    f"Error: An unexpected error occurred during streaming: {e}"
                )

    except WebSocketDisconnect:
        print("Client disconnected from chat WebSocket.")
    except Exception as e:
        print(f"An error occurred in the chat WebSocket: {e}")
        await websocket.close(code=1011, reason="An internal error occurred.")
