# app/services/generation_service.py - The Thinking Agent (v3.0)

import openai
import chromadb
import json
from flask import current_app
from . import agent_tools # <-- استيراد ترسانة الأدوات الجديدة

def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

def forge_new_code(prompt: str) -> dict:
    """
    Core function, now acting as an intelligent agent that uses tools.
    """
    try:
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "CRITICAL: OPENROUTER_API_KEY is not configured."}

        client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=90.0)
        messages = [{"role": "user", "content": prompt}]

        # --- [THE THINKING AGENT PROTOCOL] ---
        # 1. First call to the AI: "Decide if you need a tool"
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=messages,
            tools=agent_tools.tools_schema,
            tool_choice="auto",
        )
        response_message = response.choices[0].message

        # 2. Check if the AI decided to use a tool
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name in agent_tools.available_tools:
                function_to_call = agent_tools.available_tools[function_name]
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the local tool
                function_response = function_to_call(**function_args)
                
                # Return the direct result from the tool
                return {"status": "success", "code": function_response, "sources": [f"local_tool:{function_name}"], "type": "chat"}
            else:
                return {"status": "error", "message": f"AI tried to call an unknown tool: {function_name}"}

        # 3. If no tool was called, proceed with the "slow path" (Code/Chat Generation)
        else:
            # Fetch context from ChromaDB for general queries
            collection = chromadb.HttpClient(host='chroma-db', port=8000).get_or_create_collection(name="cogniforge_codebase")
            query_embedding = get_model().encode([prompt])
            results = collection.query(query_embeddings=query_embedding.tolist(), n_results=5)
            context = "\n---\n".join(results['documents'][0]) if results.get('documents') else "No specific code context found."
            sources = [meta['source'] for meta in results['metadatas'][0]] if results.get('metadatas') else []

            # Use a simple heuristic for intent, but now it's less critical
            code_keywords = ["create", "implement", "generate", "refactor", "add", "write", "fix"]
            intent = "CODE" if any(k in prompt.lower() for k in code_keywords) else "CHAT"

            if intent == "CHAT":
                final_prompt = f"You are CogniForge's Architect Assistant. Use the provided context to answer the user's question.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{prompt}"
                model_to_use = "openai/gpt-4o-mini"
            else: # CODE
                final_prompt = f"You are an expert Flask developer. Use the context to fulfill the request.\n\nCONTEXT:\n{context}\n\nREQUEST:\n{prompt}\n\nOnly output raw code."
                model_to_use = "openai/gpt-4o"

            final_completion = client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": final_prompt}]
            )
            response_text = final_completion.choices[0].message.content
            return {"status": "success", "code": response_text, "sources": sources, "type": intent.lower()}

    except Exception as e:
        return {"status": "error", "message": str(e)}