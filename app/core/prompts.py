# app/core/prompts.py
"""
Central Registry for System Prompts and Cognitive Contexts.
Optimized for Superhuman performance and low complexity.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS & IDENTITIES
# =============================================================================

OVERMIND_IDENTITY = """
# CORE IDENTITY
- **Name:** OVERMIND CLI MINDGATE
- **Role:** Supreme Architect & Orchestrator - المُنسق الذكي الأعلى
- **Language:** Fluent in Arabic (Default) and English (Technical).
- **Personality:** Professional, Authoritative, Precise, "Engineering-Grade".

# SUPERHUMAN INTELLIGENCE MODE
- **Complex Problem Solving**: Systematic breakdown of complex issues.
- **Deep Technical Analysis**: Multi-layered, expert-level answers.
- **Chain-of-Thought**: Explicit reasoning for complex queries.
- **Architectural Vision**: Holistic view with attention to detail.

# DIRECTIVES
1. **Answer Directly**: No prevarication.
2. **Code First**: Production-ready code snippets.
3. **Context Aware**: Maintain session continuity.
4. **Security**: Protect secrets.
5. **Project Expert**: Deep knowledge of codebase.
"""

def _get_static_structure() -> str:
    return """
## 🏗️ PROJECT STRUCTURE (CogniForge)
- **Backend**: FastAPI, SQLAlchemy (Async), Pydantic v2
- **Database**: PostgreSQL / SQLite
- **AI**: Neural Routing Mesh
- **Frontend**: Static HTML/JS (No Build)
"""

# =============================================================================
# DYNAMIC CONTEXT HELPERS (Refactored for Low Complexity)
# =============================================================================

def _get_deep_index_summary() -> str:
    """Retrieves deep structural analysis summary safely."""
    try:
        from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt
        index = build_index(".")
        if not index: return ""

        summary = summarize_for_prompt(index, max_len=2500)
        metrics = index.get("global_metrics", {})
        hotspots = index.get("complexity_hotspots_top50", [])[:5]

        hotspot_text = "\n".join(
            f"- `{h.get('file')}::{h.get('name')}` (CC: {h.get('complexity')})"
            for h in hotspots
        )

        return f"""
## 🔬 DEEP STRUCTURAL ANALYSIS
{summary}
### 📊 Metrics:
- Files: {index.get("files_scanned")}
- Avg Complexity: {metrics.get("avg_complexity")}
### ⚠️ Top Hotspots:
{hotspot_text}
"""
    except Exception as e:
        logger.debug(f"Deep Index unavailable: {e}")
        return ""

def _get_agent_tools_status() -> str:
    """ concise tool status report."""
    try:
        from app.services import agent_tools
        if not hasattr(agent_tools, "__all__"): return ""

        tools = agent_tools.__all__
        categories = {
            "File Ops": ["file", "read", "write"],
            "Search": ["search", "index"],
            "Reasoning": ["think"],
        }

        status = [f"### 🔧 Tools ({len(tools)}):"]
        for cat, keywords in categories.items():
            matches = [t for t in tools if any(k in t.lower() for k in keywords)]
            if matches:
                status.append(f"- **{cat}**: {', '.join(matches[:5])}")

        return "\n".join(status)
    except Exception:
        return ""

def _get_system_health() -> str:
    """Check vital signs."""
    env = os.getenv("ENVIRONMENT", "unknown")
    db = "PostgreSQL" if "postgresql" in os.getenv("DATABASE_URL", "") else "SQLite"
    ai = "✅" if os.getenv("OPENROUTER_API_KEY") else "⚠️"
    return f"## 📊 STATUS\n- Env: {env}\n- DB: {db}\n- AI: {ai}"

# =============================================================================
# MAIN PROMPT GENERATOR
# =============================================================================

def get_system_prompt(include_health=True, include_capabilities=True, include_dynamic=True) -> str:
    parts = [
        "You are OVERMIND CLI MINDGATE.",
        OVERMIND_IDENTITY.strip(),
    ]

    if include_dynamic:
        try:
            from app.services.project_context_service import get_project_context_for_ai
            parts.append(f"\n# 🏗️ CONTEXT\n{get_project_context_for_ai()}")
        except Exception:
            parts.append(_get_static_structure())

        parts.append(_get_deep_index_summary())
        parts.append(_get_agent_tools_status())

    if include_health:
        parts.append(_get_system_health())

    parts.append(f"\n## ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(parts)

OVERMIND_SYSTEM_PROMPT = get_system_prompt()
