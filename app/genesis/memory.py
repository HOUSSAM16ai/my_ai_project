"""
Genesis Memory: Context Management.
Simple sliding window memory.
"""
from __future__ import annotations

import json
from typing import Any, List

class ShortTermMemory:
    """
    Manages the conversation history.
    """

    def __init__(self):
        self.messages: List[dict] = []
        self.system_prompt = (
            "You are Genesis, a Super Intelligent Agent built on the Principle of Simplicity. "
            "You solve problems by breaking them down into simple steps. "
            "You have access to tools. Use them when needed. "
            "Answer directly and concisely."
        )

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, message: Any) -> None:
        # Convert the framework's Message object to a dict serializable for next call
        msg_dict = {"role": "assistant"}
        if message.content:
            msg_dict["content"] = message.content
        if message.tool_calls:
            msg_dict["tool_calls"] = message.tool_calls

        self.messages.append(msg_dict)

    def add_tool_result(self, tool_call_id: str, function_name: str, result: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": function_name,
            "content": result
        })

    def get_context(self) -> List[dict]:
        """Return full context including system prompt."""
        return [{"role": "system", "content": self.system_prompt}] + self.messages
