# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import time
from typing import AsyncIterator

app = FastAPI(title="CogniForge - Unified ASGI Service")

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

@app.post("/admin/api/chat/stream", summary="Admin Chat Streaming Endpoint", tags=["Admin", "Streaming"])
async def chat_stream(request: Request):
    """
    Handles POST requests to initiate a chat stream.
    Processes the incoming question and streams back the response chunk by chunk.
    """
    try:
        body = await request.json()
        question = body.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="The 'question' field is required.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    async def response_generator():
        # Here you would typically connect to your LLM or other AI service
        # For demonstration, we'll stream back a simulated response.
        for idx, part in enumerate(["Analyzing...", "Generating response...", f"Final answer for '{question}'."]):
            await asyncio.sleep(1)  # Simulate processing time
            yield f"data: {{\"chunk\": \"{part}\", \"index\": {idx}}}\n\n"

        # Signal the end of the stream
        yield "event: close\ndata: Stream ended\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")

# The root endpoint can provide basic information or API documentation link
@app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    return {"message": "Welcome to the CogniForge ASGI service. See /docs for API documentation."}
