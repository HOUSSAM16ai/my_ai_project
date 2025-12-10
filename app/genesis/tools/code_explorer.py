"""
Code Explorer Tools for Genesis.
Provides 'Superhuman' vision into the codebase: Grep, Read, Analyze.
"""
import os
import glob
import logging
import subprocess
from typing import List, Dict

logger = logging.getLogger("genesis.tools.code")

def grep_code(pattern: str, path: str = ".", context: int = 0) -> str:
    """
    Searches for a text pattern in the codebase using grep.
    Returns file paths and line numbers.

    Args:
        pattern: The text or regex to search for.
        path: The directory to search in (default: current dir).
        context: Number of lines of context to include (default: 0).
    """
    logger.info(f"Grepping for '{pattern}' in {path}")
    try:
        # Prevent searching huge dirs
        exclude_dirs = "{.git,__pycache__,node_modules,dist,build,.venv,venv}"

        cmd = [
            "grep", "-rnI",
            "--exclude-dir=" + exclude_dirs,
            pattern, path
        ]

        if context > 0:
            cmd.append(f"-C {context}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            output = result.stdout
            if len(output) > 5000:
                return output[:5000] + "\n...(Truncated, too many matches. Refine search.)"
            return output if output.strip() else "No matches found."
        elif result.returncode == 1:
            return "No matches found."
        else:
            return f"Error executing grep: {result.stderr}"

    except Exception as e:
        return f"System Error during grep: {e}"

def read_file_segment(filepath: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    Reads a specific segment of a file.

    Args:
        filepath: Path to the file.
        start_line: First line to read (1-based).
        end_line: Last line to read (-1 for end of file).
    """
    try:
        if not os.path.exists(filepath):
            return f"Error: File {filepath} not found."

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        if start_line < 1: start_line = 1
        if end_line == -1 or end_line > total_lines: end_line = total_lines

        if start_line > total_lines:
            return f"Error: Start line {start_line} exceeds file length ({total_lines})."

        segment = lines[start_line-1:end_line]
        numbered_segment = "".join([f"{i+start_line}: {line}" for i, line in enumerate(segment)])

        return numbered_segment
    except Exception as e:
        return f"Error reading file: {e}"

def list_files(path: str = ".", extension: str = None) -> str:
    """
    Lists files in a directory, optionally filtering by extension.
    """
    files = []
    try:
        for root, dirs, filenames in os.walk(path):
            # Filtering
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", "dist", ".venv"}]

            for filename in filenames:
                if extension and not filename.endswith(extension):
                    continue
                files.append(os.path.join(root, filename))

        if len(files) > 100:
             return "\n".join(files[:100]) + f"\n... (and {len(files)-100} more)"
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"

def identify_hotspots() -> str:
    """
    Identifies potentially critical areas (large files, TODOs).
    """
    report = "Codebase Hotspots Analysis:\n"

    # 1. Large Files
    large_files = []
    for root, _, filenames in os.walk("."):
        if any(x in root for x in [".git", "node_modules", "dist"]): continue
        for name in filenames:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                try:
                    with open(path, 'r') as f:
                        lines = sum(1 for _ in f)
                        if lines > 300:
                            large_files.append((path, lines))
                except: pass

    report += "\n[Large Files (>300 LOC)]:\n"
    for f, count in sorted(large_files, key=lambda x: x[1], reverse=True)[:10]:
        report += f"- {f}: {count} lines\n"

    # 2. TODOs/FIXMEs
    todos = grep_code("TODO\|FIXME")
    count_todos = len(todos.splitlines()) if "No matches" not in todos else 0
    report += f"\n[Technical Debt]: Found {count_todos} markers (TODO/FIXME).\n"

    return report
