"""
Hyper-Cognitive Tools
=====================
Reasoning, summarization, and refinement tools bridging to the LLM backend.
"""

import logging
import os

from app.core.ai_gateway import ai_gateway

from .core import tool
from .definitions import (
    CANON_THINK,
    GENERIC_THINK_MAX_ANSWER_CHARS,
    GENERIC_THINK_MAX_CHARS,
    ToolResult,
)

logger = logging.getLogger("agent_tools")

@tool(
    name=CANON_THINK,
    description="Primary cognitive tool (reasoning / analysis). Returns data.answer & data.content.",
    category="cognitive",
    capabilities=["llm", "reasoning"],
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "mode": {"type": "string", "default": "analysis"},
        },
        "required": ["prompt"],
    },
)
async def generic_think(prompt: str, mode: str = "analysis") -> ToolResult:
    clean = (prompt or "").strip()
    if not clean:
        return ToolResult(ok=False, error="EMPTY_PROMPT")
    truncated = False
    if len(clean) > GENERIC_THINK_MAX_CHARS:
        clean = clean[:GENERIC_THINK_MAX_CHARS] + "\n[TRUNCATED_INPUT]"
        truncated = True

    try:
        model_override = os.getenv("GENERIC_THINK_MODEL_OVERRIDE")
        response = await ai_gateway.generate_text(
            prompt=clean,
            model=model_override,
            system_prompt=f"You are a helpful assistant running in {mode} mode.",
        )
        answer = response.content
    except Exception as e:
        answer = f"[fallback-{mode}] AI Gateway Error: {e!s}"
        return ToolResult(
            ok=False,
            data={
                "answer": answer,
                "content": answer,
                "mode": mode,
                "fallback": True,
                "truncated_input": truncated,
                "error": str(e)
            },
        )

    if not answer.strip():
        return ToolResult(ok=False, error="EMPTY_ANSWER")
    if len(answer) > GENERIC_THINK_MAX_ANSWER_CHARS:
        answer = answer[:GENERIC_THINK_MAX_ANSWER_CHARS] + "\n[ANSWER_TRIMMED]"
    return ToolResult(
        ok=True,
        data={
            "answer": answer,
            "content": answer,
            "mode": mode,
            "fallback": False,
            "truncated_input": truncated,
        },
    )


@tool(
    name="summarize_text",
    description="Summarize provided text (delegates to generic_think).",
    category="cognitive",
    capabilities=["llm", "summarization"],
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "style": {"type": "string", "default": "concise"},
        },
        "required": ["text"],
    },
)
async def summarize_text(text: str, style: str = "concise") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    snippet = t[:8000]
    prompt = f"Summarize the following text in a {style} manner. Provide key bullet points:\n---\n{snippet}\n---"
    return await generic_think(prompt=prompt, mode="summary")


@tool(
    name="refine_text",
    description="Refine text style/tone (delegates to generic_think).",
    category="cognitive",
    capabilities=["llm", "refinement"],
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "tone": {"type": "string", "default": "professional"},
        },
        "required": ["text"],
    },
)
async def refine_text(text: str, tone: str = "professional") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    prompt = (
        f"Refine the following text to a {tone} tone while preserving meaning. "
        f"Return only the improved text without commentary:\n---\n{t[:8000]}\n---"
    )
    return await generic_think(prompt=prompt, mode="refine")
