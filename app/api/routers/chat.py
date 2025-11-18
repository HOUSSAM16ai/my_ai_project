# app/api/routers/chat.py
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.ai_gateway import AIClient, get_ai_client


router = APIRouter(
    tags=["Chat"],
)


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    ai_client: AIClient = Depends(get_ai_client),
):
    """
    The main WebSocket endpoint for the admin chat.
    This has been migrated to use the ENERGY-ENGINE for AI communication.
    """
    await websocket.accept()

    try:
        while True:
            question = await websocket.receive_text()

            try:
                async for chunk in ai_client.stream_chat([{"role": "user", "content": question}]):
                    await websocket.send_text(json.dumps(chunk))
            except Exception as e:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "payload": {"error": f"Failed to connect to AI service: {e}"},
                        }
                    )
                )

    except WebSocketDisconnect:
        print("Client disconnected from chat WebSocket.")
    except Exception as e:
        print(f"An error occurred in the chat WebSocket: {e}")
        await websocket.close(code=1011, reason="An internal error occurred.")
