# app/services/agent_tools.py - The Agent's Tool Arsenal

import json
from . import repo_inspector_service
from . import system_service

# --- Tool Implementations ---

def get_project_summary():
    """
    Returns a high-level summary of the project, including file count,
    top file extensions, and total lines of code.
    Use this when the user asks a general question about the project's size or composition.
    """
    summary = repo_inspector_service.get_project_summary()
    # Format the output as a human-readable string
    return json.dumps(summary, indent=2)

def query_file_content(file_path: str):
    """
    Retrieves the full content of a specific file from the project's indexed memory or disk.
    Use this when the user asks 'What is in file X?' or 'Show me the code for X'.
    """
    result = system_service.query_file(file_path)
    return result.get("content", f"Error: Could not retrieve content for {file_path}.")

# --- Tool Definitions for the AI ---

# This is a mapping of function names to the actual Python functions.
available_tools = {
    "get_project_summary": get_project_summary,
    "query_file_content": query_file_content,
}

# This is the schema definition that the AI model will see.
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
]