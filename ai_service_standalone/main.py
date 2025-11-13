
import asyncio
import logging
import os

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# This is now a self-contained FastAPI application.
# All necessary components are included in this file.

# --- Mock LLM Client ---
class MockChoice:
    def __init__(self, content):
        self.delta = self
        self.content = content

class MockStream:
    def __init__(self, text):
        self.words = text.split()
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.words):
            word = self.words[self.index]
            self.index += 1
            # Yield a choice object similar to the real API
            return type('obj', (object,), {'choices': [MockChoice(word + " ")]})
        else:
            raise StopIteration

class MockCompletions:
    def create(self, model, messages, stream, temperature, max_tokens):
        last_message = messages[-1]['content']
        return MockStream(f"This is a streamed response to '{last_message}'")

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockLLMClient:
    def __init__(self):
        self.chat = MockChat()

def get_llm_client():
    # In a real scenario, this would initialize a client like OpenAI's or a custom one
    return MockLLMClient()

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- JWT Configuration ---
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key")
ALGORITHM = "HS256"

# --- FastAPI Application ---
app = FastAPI()

async def get_current_user(token: str):
    """Decodes the JWT to get the user ID."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        return user_id
    except jwt.ExpiredSignatureError:
        logger.warning("Authentication failed: Token has expired.")
        return None
    except jwt.PyJWTError as e:
        logger.error(f"Authentication failed: {e}")
        return None

async def stream_ai_response(question: str, websocket: WebSocket):
    """Streams the AI response over the WebSocket."""
    try:
        llm_client = get_llm_client()
        messages = [{"role": "user", "content": question}]

        stream = llm_client.chat.completions.create(
            model="mock-model",
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=150
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if content:
                await websocket.send_text(content)
                await asyncio.sleep(0.05) # Control the speed of streaming
    except Exception as e:
        logger.error(f"Error during AI streaming: {e}", exc_info=True)
        await websocket.send_text("Error: Could not process your request.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for handling chat."""
    await websocket.accept()

    # First message should be the auth token
    token = await websocket.receive_text()
    user = await get_current_user(token)

    if not user:
        await websocket.close(code=1008) # Policy Violation
        return

    logger.info(f"User {user} connected.")
    await websocket.send_text("Authentication successful. Ready for questions.")

    try:
        while True:
            # Wait for questions from the client
            question = await websocket.receive_text()
            logger.info(f"Received question from user {user}: {question}")

            # Stream the response
            await stream_ai_response(question, websocket)
    except WebSocketDisconnect:
        logger.info(f"Client {user} disconnected.")
    except Exception as e:
        logger.error(f"An unexpected error occurred for user {user}: {e}", exc_info=True)
