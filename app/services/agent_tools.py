# app/services/agent_tools.py - The Context-Aware Tool Arsenal (v2.4 - Final)

import json
from . import repo_inspector_service
from . import system_service
from .refactoring_tool import RefactorTool
from .llm_client_service import get_llm_client

# --- [CONTEXT-AWARE INITIALIZATION PROTOCOL] ---
# We define helper functions to initialize tools that need the app context
# ONLY when they are actually called. This solves the startup error.

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
    # Initialize the tool on demand, inside the function call.
    refactor_tool = _get_refactor_tool()
    
    result = refactor_tool.apply_code_refactoring(
        file_path=file_path,
        requested_changes=requested_changes,
        dry_run=True # Always preview first for safety!
    )
    if result.changed:
        return f"PREVIEW of changes for '{result.file_path}':\n\n{result.diff}"
    else:
        return result.message

# --- Tool Definitions for the AI ---

# This maps the AI-callable function names to our Python functions.
available_tools = {
    "get_project_summary": get_project_summary,
    "query_file_content": query_file_content,
    "apply_code_refactoring": apply_code_refactoring,
}

# This is the schema definition that the AI model sees.
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_project_summary",
            "description": "Returns a summary of the project: file count, top extensions, and lines of code.",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_file_content",
            "description": "Retrieves the full content of a specific file from the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file, e.g., 'app/models.py'."
                    }
                },
                "required": ["file_path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_code_refactoring",
            "description": "Refactors a specific file based on a user's request and shows a preview of the changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file that needs refactoring."
                    },
                    "requested_changes": {
                        "type": "string",
                        "description": "A clear, specific description of the changes to be made."
                    }
                },
                "required": ["file_path", "requested_changes"],
            },
        }
    },
]