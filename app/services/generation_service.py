# app/services/generation_service.py - The Synthesizing Architect (v7.2 - Object-Aware & Final)

from .llm_client_service import get_llm_client
from .system_service import find_related_context # We no longer need this direct import
from . import agent_tools
import json

def forge_new_code(prompt: str, conversation_history: list = None) -> dict:
    """
    The synthesizing core of our AI. It uses a multi-step reasoning loop,
    guided by a master prompt and a disciplined tool schema, to achieve the user's true intent.
    This version is object-aware, correctly handling modern API responses.
    """
    # Initialize the conversation with the master instructions that define the AI's persona and logic.
    if conversation_history is None:
        master_prompt = f"""
        You are the hyper-intelligent Strategic Architect AI of the CogniForge project.
        Your goal is to assist the user by deeply understanding their true INTENT.
        You have two capabilities: DEEP REASONING and TOOL USE.

        - For questions requiring explanation, summarization, or creative thought (e.g., "what is the purpose of...", "explain how..."), your process MUST be:
          1. Use the 'query_file_content' tool to gather information.
          2. In the next step, analyze the tool's output and provide a synthesized, high-level answer.
        
        - For direct commands (e.g., "get the content of..."), you may use a tool and return the result directly.
        """
        conversation_history = [{"role": "system", "content": master_prompt}]

    try:
        client = get_llm_client()
        # The 'messages' list will be a mix of dicts (our history) and pydantic models (from OpenAI)
        messages: list = conversation_history + [{"role": "user", "content": prompt}]
        
        # --- [MULTI-STEP REASONING LOOP] ---
        for i in range(5):
            print(f"--- Thinking Step {i+1} ---")

            # Convert all messages to dictionaries before sending, ensuring compatibility.
            messages_for_api = [
                msg if isinstance(msg, dict) else msg.dict() for msg in messages
            ]

            response = client.chat.completions.create(
                model="openai/gpt-4o",
                messages=messages_for_api,
                tools=agent_tools.tools_schema,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Append the AI's response (which is a model object) to our list
            messages.append(response_message)

            if tool_calls:
                print(f"Decision: Tool usage identified. Executing {len(tool_calls)} tool(s).")
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    if function_name in agent_tools.available_tools:
                        function_to_call = agent_tools.available_tools[function_name]
                        function_args = json.loads(tool_call.function.arguments)
                        
                        function_response = function_to_call(**function_args)
                        
                        # Append the tool's result as a dictionary
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response, indent=2, ensure_ascii=False) if isinstance(function_response, dict) else str(function_response),
                        })
                    else:
                        messages.append({
                            "tool_call_id": tool_call.id, "role": "tool", "name": function_name,
                            "content": f"Error: Tool '{function_name}' not found.",
                        })
                
                continue

            else:
                print("Decision: Deep reasoning complete. Final answer generated.")
                final_answer = response_message.content
                
                # --- [THE OBJECT-AWARE FIX] ---
                # Check for tool usage by iterating through the mixed list of dicts and objects.
                sources = ["reasoning"]
                for msg in messages:
                    # Check if it's a dict with the right role, OR an object with the right attribute
                    is_tool_dict = isinstance(msg, dict) and msg.get("role") == "tool"
                    is_tool_object = hasattr(msg, 'tool_calls') and msg.tool_calls is not None
                    
                    if is_tool_dict or is_tool_object:
                        sources.append("local_tool")
                        break # Found one, no need to check further
                # --- نهاية الإصلاح الخارق ---
                    
                return {
                    "status": "success",
                    "code": final_answer,
                    "sources": list(set(sources)),
                    "type": "synthesized_response"
                }
        
        return {"status": "error", "message": "Agent exceeded maximum thinking steps."}

    except Exception as e:
        return {"status": "error", "message": f"Forge operation failed: {e}"}