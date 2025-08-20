# app/services/generation_service.py - The Thinking Agent (v3.2 - Final)

import openai
import chromadb
import json
from flask import current_app

# --- [THE DECOUPLING PROTOCOL] ---
# We import the tool arsenal and the central client factory.
from . import agent_tools
from .llm_client_service import get_llm_client

def get_model():
    """Helper to load the embedding model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

def forge_new_code(prompt: str) -> dict:
    """
    Core function, acting as an intelligent agent that uses tools.
    It now gets its LLM client from a dedicated, central service and lets
    the AI decide the best course of action (use a tool or respond directly).
    """
    try:
        # Initialize the client safely inside the function call
        client = get_llm_client()
        messages = [{"role": "user", "content": prompt}]

        # --- [THE THINKING AGENT PROTOCOL] ---
        # 1. First call to the AI: "Analyze the prompt and decide if a tool from
        #    the provided list can help. If so, call it. If not, respond directly."
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=messages,
            tools=agent_tools.tools_schema,
            tool_choice="auto",
        )
        response_message = response.choices[0].message

        # 2. Check if the AI decided to use a tool
        tool_calls = response_message.tool_calls
        if tool_calls:
            # We will process the first tool call.
            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name in agent_tools.available_tools:
                function_to_call = agent_tools.available_tools[function_name]
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the local tool with its arguments
                function_response = function_to_call(**function_args)
                
                return {
                    "status": "success",
                    "code": function_response,
                    "sources": [f"local_tool:{function_name}"],
                    "type": "tool_response"
                }
            else:
                return {"status": "error", "message": f"AI tried to call an unknown tool: {function_name}"}

        # 3. If no tool was called, this is a general query. Proceed with the "slow path".
        else:
            final_response = response_message.content
            # We can still try to find context for this general response
            sources = []
            try:
                collection = chromadb.HttpClient(host='chroma-db', port=8000).get_or_create_collection(name="cogniforge_codebase")
                query_embedding = get_model().encode([prompt])
                results = collection.query(query_embeddings=query_embedding.tolist(), n_results=3)
                if results.get('metadatas') and results['metadatas'][0]:
                    sources = [meta.get('source', '') for meta in results['metadatas'][0]]
            except Exception:
                # Fail silently if context retrieval fails, as it's optional for chat
                pass

            return {"status": "success", "code": final_response, "sources": sources, "type": "chat"}

    except Exception as e:
        # Catch any exception, including the ValueError from get_llm_client if the key is missing
        return {"status": "error", "message": str(e)}