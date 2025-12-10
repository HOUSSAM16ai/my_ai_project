"""
Genesis Core: The Agent Implementation.
Implements the Think -> Plan -> Act -> Observe loop.
Refactored to include Codebase Intelligence (Context Injection).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from app.genesis.brain import Cortex
from app.genesis.memory import ShortTermMemory
from app.genesis.registry import ToolRegistry
from app.services.chat.context_service import get_context_service

logger = logging.getLogger("genesis.core")


class GenesisAgent:
    """
    A simplified Super Agent based on First Principles.

    Structure:
    - Cortex: The Brain (LLM)
    - Memory: Context Management
    - Tools: Capabilities
    - Loop: The Control Flow
    """

    def __init__(self, model: str = "gpt-4o"):
        self.cortex = Cortex(model=model)
        self.memory = ShortTermMemory()
        self.tools = ToolRegistry()
        self.max_steps = 10
        self._inject_context()

    def _inject_context(self):
        """Injects codebase knowledge into the agent's memory."""
        try:
            context_service = get_context_service()
            # We override the default system prompt in memory with the smart one
            smart_prompt = context_service.get_context_system_prompt()
            self.memory.system_prompt = smart_prompt
            logger.info("Genesis: Codebase Context Injected Successfully.")
        except Exception as e:
            logger.warning(f"Genesis: Failed to inject context: {e}")

    def register_tool(self, func: Callable) -> None:
        """Register a new capability."""
        self.tools.register(func)

    def run(self, user_input: str) -> str:
        """
        The Main Execution Loop.
        1. Input -> Memory
        2. Loop:
           a. Construct Context (Memory + Tools)
           b. Think (LLM -> Decision)
           c. Act (Tool Execution) or Finish
           d. Observe (Tool Output -> Memory)
        """
        logger.info(f"Genesis Agent received input: {user_input}")
        self.memory.add_user_message(user_input)

        for step in range(self.max_steps):
            logger.info(f"Step {step + 1}/{self.max_steps}")

            # 1. Think
            response = self.cortex.think(
                messages=self.memory.get_context(),
                tools=self.tools.get_definitions()
            )

            # 2. Decide
            if response.tool_calls:
                # 3. Act
                for tool_call in response.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse arguments for {function_name}")
                        continue

                    logger.info(f"Acting: {function_name}({arguments})")

                    # Execute
                    try:
                        result = self.tools.execute(function_name, **arguments)
                    except Exception as e:
                        result = f"Error executing tool {function_name}: {e}"
                        logger.error(result)

                    # 4. Observe
                    self.memory.add_tool_result(
                        tool_call_id=tool_call.id,
                        function_name=function_name,
                        result=str(result)
                    )

                # Add the assistant's request to memory AFTER execution loop
                # (to keep history linear: User -> Assistant(Calls) -> Tool(Results) -> Assistant(Reply))
                self.memory.add_assistant_message(response)

            else:
                # No tool calls? We are done.
                final_answer = response.content
                self.memory.add_assistant_message(response)
                logger.info("Task completed.")
                return final_answer or "I completed the task but have no text output."

        return "Max steps reached without final answer."
