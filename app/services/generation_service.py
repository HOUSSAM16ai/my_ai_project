# app/services/generation_service.py - The Thinking Agent (v3.1 - Decoupled)

import openai
import chromadb
import json
from flask import current_app

# --- [THE DECOUPLING PROTOCOL] ---
from . import agent_tools
from .llm_client_service import get_llm_client # <-- استيراد من الوزارة الجديدة

def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

def forge_new_code(prompt: str) -> dict:
    """
    Core function, acting as an intelligent agent that uses tools.
    It now gets its LLM client from a dedicated, central service.
    """
    try:
        client = get_llm_client() # <-- استدعاء العميل المركزي
        messages = [{"role": "user", "content": prompt}]

        # --- [THE THINKING AGENT PROTOCOL] ---
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=messages,
            tools=agent_tools.tools_schema,
            tool_choice="auto",
        )
        response_message = response.choices[0].message

        tool_calls = response_message.tool_calls
        if tool_calls:
            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name in agent_tools.available_tools:
                function_to_call = agent_tools.available_tools[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                return {"status": "success", "code": function_response, "sources": [f"local_tool:{function_name}"], "type": "tool_response"}
            else:
                return {"status": "error", "message": f"AI tried to call an unknown tool: {function_name}"}
        else:
            final_response = response_message.content
            # ... (منطق جلب السياق يمكن أن يضاف هنا إذا أردنا)
            return {"status": "success", "code": final_response, "sources": [], "type": "chat"}

    except Exception as e:
        return {"status": "error", "message": str(e)}