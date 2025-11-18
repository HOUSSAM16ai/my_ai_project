# app/api/routers/chat.py
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.factories import get_ai_gateway
from app.gateways.ai_service_gateway import AIServiceGateway

router = APIRouter(
    tags=["Chat"],
)


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    gateway: AIServiceGateway = Depends(get_ai_gateway),
):
    """
    The main WebSocket endpoint for the admin chat.
    Handles the connection, receives messages, and streams back AI responses
    using a dependency-injected AI Service Gateway.
    """
    await websocket.accept()
    user_id = "admin_user_websocket"  # Placeholder for authenticated user

    try:
        while True:
            question = await websocket.receive_text()

            async def response_generator():
                try:
                    # Stream the response directly from the gateway
                    for chunk in gateway.stream_chat(question, None, user_id):
                        yield chunk
                except Exception as e:
                    yield {
                        "type": "error",
                        "payload": {"error": f"Failed to connect to AI service: {e}"},
                    }

            async for chunk in response_generator():
                await websocket.send_text(json.dumps(chunk))

    except WebSocketDisconnect:
        print("Client disconnected from chat WebSocket.")
    except Exception as e:
        print(f"An error occurred in the chat WebSocket: {e}")
        await websocket.close(code=1011, reason="An internal error occurred.")
