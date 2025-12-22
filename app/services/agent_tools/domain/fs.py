"""
File System Tools Implementation.
"""
import os
import glob
from pathlib import Path
from typing import Any
from app.services.agent_tools.new_core import tool
import asyncio

# Safety Configuration
PROJECT_ROOT = os.path.abspath(os.getenv("AGENT_TOOLS_PROJECT_ROOT", "/app"))

def _safe_path(path: str) -> str:
    """
    Sanitize and validate path to prevent directory traversal.
    """
    # Normalize path
    target = os.path.abspath(os.path.join(PROJECT_ROOT, path))

    # Check if target is within root
    if not target.startswith(PROJECT_ROOT):
        raise PermissionError(f"Access denied: Path '{path}' is outside project root.")

    return target

# Async Context Manager Wrapper
class AsyncFileContext:
    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
        self.file = None

    async def __aenter__(self):
        loop = asyncio.get_running_loop()
        self.file = await loop.run_in_executor(None, open, self.path, self.mode)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.file.close)

    async def read(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.file.read)

    async def write(self, data):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.file.write, data)

def asyncio_open(path: str, mode: str):
    """Factory to return the async context manager."""
    return AsyncFileContext(path, mode)


@tool(
    name="read_file",
    description="Reads the content of a file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."}
        },
        "required": ["path"]
    }
)
async def read_file(path: str) -> str:
    """Reads a file safely."""
    safe_target = _safe_path(path)
    if not os.path.exists(safe_target):
        raise FileNotFoundError(f"File not found: {path}")

    async with asyncio_open(safe_target, "r") as f:
        content = await f.read()
    return content

@tool(
    name="write_file",
    description="Writes content to a file (overwrites).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."},
            "content": {"type": "string", "description": "Content to write."}
        },
        "required": ["path", "content"]
    }
)
async def write_file(path: str, content: str) -> str:
    """Writes to a file safely."""
    safe_target = _safe_path(path)

    # Ensure directory exists
    os.makedirs(os.path.dirname(safe_target), exist_ok=True)

    async with asyncio_open(safe_target, "w") as f:
        await f.write(content)

    return f"File written successfully: {path}"

@tool(
    name="list_files",
    description="Lists files in a directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (default: .)."}
        }
    }
)
async def list_files(path: str = ".") -> list[str]:
    """Lists files safely."""
    safe_target = _safe_path(path)

    if not os.path.isdir(safe_target):
        raise NotADirectoryError(f"Not a directory: {path}")

    # Use glob for simple listing or os.listdir
    # Return relative paths for cleaner output
    files = []
    loop = asyncio.get_running_loop()

    def _walk():
        result = []
        for root, _, filenames in os.walk(safe_target):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, safe_target)
                result.append(rel_path)
                if len(result) > 1000:
                    break
            if len(result) > 1000:
                break
        return result

    files = await loop.run_in_executor(None, _walk)
    return files
