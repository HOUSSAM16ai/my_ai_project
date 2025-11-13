# ai_service_standalone/main.py
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

app = FastAPI()

@app.post("/api/v1/chat/stream")
async def chat_stream(request: Request):
    body = await request.json()
    question = body.get("question")
    # conversation_id is not used in this simplified example, but is kept for compatibility
    # conversation_id = body.get("conversation_id")

    async def generate():
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a world class developer."),
            ("user", "{input}")
        ])
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        async for chunk in chain.astream({"input": question}):
            yield f"data: {json.dumps({'type': 'data', 'payload': {'content': chunk}})}\n\n"

        # Send an end-of-stream message
        yield f"data: {json.dumps({'type': 'end', 'payload': {'conversation_id': 'mock_conv_123'}})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
