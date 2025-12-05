"""
Hyper-Cognitive Tools
=====================
Reasoning, summarization, and refinement tools bridging to the LLM backend.
"""
import os
import logging

from .core import tool, CANON_THINK
from .definitions import (
    GENERIC_THINK_MAX_ANSWER_CHARS,
    GENERIC_THINK_MAX_CHARS,
    ToolResult,
)

logger = logging.getLogger("agent_tools")

# LLM / Cognitive ------------------------------------------------------------
try:
    from app.services import generation_service as maestro
except Exception:
    maestro = None
    logger.warning(
        "LLM backend (generation_service) not available; generic_think fallback mode active."
    )


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
def generic_think(prompt: str, mode: str = "analysis") -> ToolResult:
    clean = (prompt or "").strip()
    if not clean:
        return ToolResult(ok=False, error="EMPTY_PROMPT")
    truncated = False
    if len(clean) > GENERIC_THINK_MAX_CHARS:
        clean = clean[:GENERIC_THINK_MAX_CHARS] + "\n[TRUNCATED_INPUT]"
        truncated = True
    if not maestro:
        answer = f"[fallback-{mode}] {clean[:400]}"
        return ToolResult(
            ok=True,
            data={
                "answer": answer,
                "content": answer,
                "mode": mode,
                "fallback": True,
                "truncated_input": truncated,
            },
        )
    model_override = os.getenv("GENERIC_THINK_MODEL_OVERRIDE")
    candidate_methods = ["generate_text", "forge_new_code", "run", "complete", "structured"]
    response = None
    last_err = None
    for m in candidate_methods:
        if hasattr(maestro, m):
            try:
                method = getattr(maestro, m)
                kwargs = {"prompt": clean}
                if model_override:
                    kwargs["model"] = model_override
                response = method(**kwargs)
                break
            except Exception as e:
                last_err = e
                continue
    if response is None:
        return ToolResult(
            ok=False, error=f"LLM_BACKEND_FAILURE: {last_err}" if last_err else "NO_LLM_METHOD"
        )

    if isinstance(response, str):
        answer = response
    elif isinstance(response, dict):
        answer = (
            response.get("answer")
            or response.get("content")
            or response.get("text")
            or response.get("output")
            or ""
        )
    else:
        answer = str(response)

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
def summarize_text(text: str, style: str = "concise") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    snippet = t[:8000]
    prompt = f"Summarize the following text in a {style} manner. Provide key bullet points:\n---\n{snippet}\n---"
    return generic_think(prompt=prompt, mode="summary")


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
def refine_text(text: str, tone: str = "professional") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    prompt = (
        f"Refine the following text to a {tone} tone while preserving meaning. "
        f"Return only the improved text without commentary:\n---\n{t[:8000]}\n---"
    )
    return generic_think(prompt=prompt, mode="refine")
