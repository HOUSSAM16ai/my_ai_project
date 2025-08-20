# app/services/agent_tools.py - The Disciplined Arsenal (v3.0 - Final)

import json
from . import repo_inspector_service
from . import system_service
from .refactoring_tool import RefactorTool
from .llm_client_service import get_llm_client

# --- [CONTEXT-AWARE INITIALIZATION PROTOCOL] ---
def _get_refactor_tool():
    """Initializes and returns the refactor tool just-in-time."""
    llm_client = get_llm_client()
    return RefactorTool(llm_client)

# --- Tool Implementations (The functions the AI can call) ---
def get_project_summary():
    """Returns a high-level summary of the project."""
    summary = repo_inspector_service.get_project_summary()
    return json.dumps(summary, indent=2)

def query_file_content(file_path: str):
    """Retrieves the full content of a specific file."""
    result = system_service.query_file(file_path)
    return result.get("content", f"Error: Could not retrieve content for {file_path}.")

def apply_code_refactoring(file_path: str, requested_changes: str):
    """
    Intelligently refactors a file and returns a preview of the changes.
    """
    refactor_tool = _get_refactor_tool()
    result = refactor_tool.apply_code_refactoring(
        file_path=file_path,
        requested_changes=requested_changes,
        dry_run=True
    )
    if result.changed:
        return f"PREVIEW of changes for '{result.file_path}':\n\n{result.diff}"
    else:
        return result.message

# --- Tool Definitions for the AI ---
available_tools = {
    "get_project_summary": get_project_summary,
    "query_file_content": query_file_content,
    "apply_code_refactoring": apply_code_refactoring,
}

# --- [THE DISCIPLINED SCHEMA - THE ULTIMATE FIX] ---
# This is the schema with hyper-specific instructions to guide the AI's choices.
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_project_summary",
            "description": "Use this function ONLY for requests about general project statistics, such as total file count, code lines, or language distribution. Do NOT use it to answer questions about specific files or their purpose.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_file_content",
            "description": "Use this function to read the full, raw content of a specific file. This is the necessary first step for any task that requires understanding, explaining, summarizing, or refactoring a file. Use it when the user asks 'what is the purpose of...' a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The full, relative path to the file to be read, e.g., 'app/services/system_service.py'.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_code_refactoring",
            "description": "Analyzes the code in a given file, applies specific requested changes, and returns a preview of the modifications (a diff). This should be used AFTER reading the file content to understand it first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file that needs refactoring.",
                    },
                    "requested_changes": {
                        "type": "string",
                        "description": "A clear, specific description of the changes to be made to the code.",
                    },
                },
                "required": ["file_path", "requested_changes"],
            },
        },
    },
]