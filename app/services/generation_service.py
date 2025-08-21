# app/services/generation_service.py - The Self-Archiving, Enterprise-Ready Architect (v9.0)

import json
from flask import current_app
from app import db
from app.models import Message
from .llm_client_service import get_llm_client
from . import agent_tools

def _save_message_to_db(conversation_id: str, role: str, content: str, tool_name: str = None):
    """A helper function to write a message to the immortal memory."""
    if not conversation_id:
        current_app.logger.warning("Attempted to save message but conversation_id is missing.")
        return
    try:
        new_message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_name=tool_name
        )
        db.session.add(new_message)
        current_app.logger.info(f"Message (Role: {role}) queued for conversation {conversation_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to queue message for conversation {conversation_id}: {e}", exc_info=True)

def forge_new_code(prompt: str, conversation_history: list = None, conversation_id: str = None) -> dict:
    """
    The synthesizing core of our AI. It archives its entire thought process
    into the immortal database for future learning, using enterprise-grade best practices.
    """
    # --- [CENTRALIZED COMMAND PROTOCOL] ---
    # Load strategic configuration from the central constitution (config.py).
    model_name = current_app.config.get('DEFAULT_AI_MODEL', 'openai/gpt-4o')
    max_steps = current_app.config.get('AGENT_MAX_STEPS', 5)

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
    
    # --- [IMMORTAL MEMORY PROTOCOL] - Record the user's initial prompt ---
    _save_message_to_db(conversation_id, "user", prompt)

    try:
        client = get_llm_client()
        messages: list = conversation_history + [{"role": "user", "content": prompt}]
        
        for i in range(max_steps):
            current_app.logger.info(f"--- Thinking Step {i+1}/{max_steps} for ConvID: {conversation_id} ---")

            messages_for_api = [
                msg if isinstance(msg, dict) else msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict()
                for msg in messages
            ]

            response = client.chat.completions.create(model=model_name, messages=messages_for_api, tools=agent_tools.tools_schema, tool_choice="auto")
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            messages.append(response_message)

            # Record the AI's thought process to the immortal archive
            _save_message_to_db(conversation_id, "assistant", response_message.model_dump_json())

            if tool_calls:
                current_app.logger.info(f"Decision: Tool usage identified. Executing {len(tool_calls)} tool(s).")
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    try:
                        if function_name in agent_tools.available_tools:
                            function_to_call = agent_tools.available_tools[function_name]
                            function_args = json.loads(tool_call.function.arguments)
                            
                            function_response = function_to_call(**function_args)
                            
                            tool_content = json.dumps(function_response, indent=2, ensure_ascii=False) if isinstance(function_response, dict) else str(function_response)
                            
                            _save_message_to_db(conversation_id, "tool", tool_content, tool_name=function_name)
                            messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": tool_content})
                        else:
                            raise ValueError(f"Tool '{function_name}' not found in available_tools.")
                    except (json.JSONDecodeError, TypeError, ValueError) as e:
                        error_content = f"Error: Failed to process tool '{function_name}'. Details: {e}"
                        current_app.logger.warning(error_content)
                        _save_message_to_db(conversation_id, "tool", error_content, tool_name=function_name)
                        messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": error_content})
                
                continue

            else:
                current_app.logger.info("Decision: Deep reasoning complete. Final answer generated.")
                final_answer = response_message.content
                
                # Record the final answer
                _save_message_to_db(conversation_id, "assistant", final_answer)
                db.session.commit()

                sources = ["reasoning"]
                for msg in messages:
                    is_tool_msg = (isinstance(msg, dict) and msg.get("role") == "tool") or (hasattr(msg, 'tool_calls') and msg.tool_calls is not None)
                    if is_tool_msg:
                        sources.append("local_tool")
                        break
                    
                return {"status": "success", "code": final_answer, "sources": list(set(sources)), "type": "synthesized_response"}
        
        db.session.commit()
        return {"status": "error", "message": f"Agent exceeded maximum thinking steps ({max_steps})."}

    except Exception as e:
        current_app.logger.error(f"Forge operation failed catastrophically: {e}", exc_info=True)
        db.session.rollback()
        return {"status": "error", "message": f"Forge operation failed: {e}"}