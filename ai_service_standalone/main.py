# ai_service_standalone/main.py
"""
AI Service - FastAPI Implementation
===================================
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
from typing import Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator


# --- Models ---
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None

    @field_validator("question", mode="before")
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


# --- JWT Configuration ---
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key")
ALGORITHM = "HS256"

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI()


# --- Security ---
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# --- AI Service Logic ---
async def stream_ai_response(question: str):
    """
    A mock generator that streams a response.
    """
    words = f"This is a streamed response to your question: '{question}'".split()
    for word in words:
        yield {"type": "data", "payload": {"content": f"{word} "}}
        await asyncio.sleep(0.1)

    yield {"type": "end", "payload": {"conversation_id": "conv_12345"}}


# --- API Endpoint ---
@app.post("/api/v1/chat/stream")
async def stream_chat(chat_request: ChatRequest, user_id: str = Depends(get_current_user)):
    async def response_generator():
        async for chunk in stream_ai_response(chat_request.question):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")
