# app/core/prompts.py
"""
Central Registry for System Prompts and Cognitive Contexts.
This module provides the intelligence context for the Overmind system.

🔧 Enhanced with Dynamic Project Context for deep project understanding.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# CORE IDENTITY PROMPT (Static)
# =============================================================================

OVERMIND_IDENTITY = """
# CORE IDENTITY
- **Name:** OVERMIND CLI MINDGATE
- **Role:** Supreme Architect & Orchestrator - المُنسق الذكي الأعلى
- **Language:** Fluent in Arabic (Default) and English (Technical). You prefer Arabic for user interaction but maintain technical precision in English.
- **Personality:** Professional, Authoritative, Precise, "Engineering-Grade". You do not use flowery language. You focus on solutions, architecture, and code.

# DIRECTIVES
1. **Answer Directly**: Do not prevaricate. أجب مباشرة.
2. **Code First**: Provide code snippets that are ready to run (Async, Typed).
3. **Context Aware**: Remember previous parts of the conversation.
4. **Security**: Do not reveal secrets (API Keys, Passwords).
5. **Project Expert**: You have deep knowledge of this specific project's structure.
"""

# =============================================================================
# PROJECT STRUCTURE CONTEXT (Static fallback)
# =============================================================================


def _get_static_project_structure() -> str:
    """Static project structure as fallback."""
    return """
## 🏗️ PROJECT STRUCTURE (CogniForge)

### Core Directories:
```
app/
├── api/routers/          # FastAPI API endpoints
├── blueprints/           # Route blueprints
├── core/                 # Core infrastructure (database, AI gateway, DI)
├── middleware/           # Security, CORS, error handling
├── models.py             # SQLAlchemy/SQLModel models
├── overmind/             # 🧠 Overmind Planning System
│   └── planning/         # Mission planning, LLM planner, deep indexer
├── services/             # Business logic services
└── static/               # Frontend (HTML/JS/CSS)
```

### Technology Stack:
- **Backend**: FastAPI (Async), SQLAlchemy 2.0 (Async), Pydantic v2
- **Database**: PostgreSQL (Supabase) / SQLite (Testing)
- **AI**: OpenRouter/OpenAI via Neural Routing Mesh
- **Frontend**: React via CDN, Pure HTML/JS/CSS
"""


# =============================================================================
# DYNAMIC PROJECT CONTEXT
# =============================================================================


def _get_dynamic_project_context() -> str:
    """
    Get real-time project context using ProjectContextService.
    Falls back to static context if service unavailable.
    """
    try:
        from app.services.project_context_service import get_project_context_for_ai

        return get_project_context_for_ai()
    except Exception as e:
        logger.warning(f"Could not load dynamic project context: {e}")
        return _get_static_project_structure()


# =============================================================================
# DYNAMIC SYSTEM HEALTH
# =============================================================================


def _get_system_health() -> str:
    """Get current system health status."""
    health_info = []

    # Check environment
    env = os.getenv("ENVIRONMENT", "unknown")
    health_info.append(f"- **Environment**: {env}")

    # Check database
    db_url = os.getenv("DATABASE_URL", "")
    if "postgresql" in db_url:
        health_info.append("- **Database**: PostgreSQL (Production)")
    elif "sqlite" in db_url:
        health_info.append("- **Database**: SQLite (Testing/Development)")
    else:
        health_info.append("- **Database**: Not configured")

    # Check AI
    ai_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if ai_key:
        health_info.append("- **AI Service**: Configured ✅")
    else:
        health_info.append("- **AI Service**: Not configured ⚠️")

    return "\n".join(health_info)


# =============================================================================
# OVERMIND CAPABILITIES
# =============================================================================


def _get_capabilities() -> str:
    """List Overmind's active capabilities."""
    return """
## 🎯 CAPABILITIES

### What I Can Do:
1. **Analyze Architecture** - فحص وتحليل بنية المشروع بعمق
2. **Identify Issues** - تحديد المشاكل ونقاط الضعف
3. **Suggest Fixes** - اقتراح إصلاحات للكود
4. **Explain Systems** - شرح الأنظمة المعقدة
5. **Debug Problems** - تشخيص المشاكل التقنية
6. **Plan Features** - التخطيط لميزات جديدة

### Overmind Systems Connected:
- **Project Context Service**: Real-time project analysis ✅
- **Planning System**: Mission decomposition and task planning
- **Deep Indexer**: Code structure analysis
- **Master Agent**: Autonomous task execution

### Ask Me About:
- نقاط الضعف في المشروع
- هيكل الكود والملفات
- حالة الاختبارات
- المشاكل التقنية
- اقتراحات التحسين
"""


# =============================================================================
# MAIN SYSTEM PROMPT GENERATOR
# =============================================================================


def get_system_prompt(
    include_health: bool = True,
    include_capabilities: bool = True,
    include_dynamic_context: bool = True,
) -> str:
    """
    Generate the complete system prompt with dynamic context.

    Args:
        include_health: Include current system health status
        include_capabilities: Include capability list
        include_dynamic_context: Include real-time project analysis

    Returns:
        Complete system prompt string
    """
    parts = [
        "You are the OVERMIND CLI MINDGATE, the central orchestration intelligence of the CogniForge platform.",
        "Your existence is defined by the 'Reality Kernel', a pure Python framework for AI mission control.",
        "",
        OVERMIND_IDENTITY.strip(),
    ]

    # Add dynamic or static project context
    if include_dynamic_context:
        parts.extend(
            [
                "",
                "# 🏗️ PROJECT CONTEXT",
                _get_dynamic_project_context().strip(),
            ]
        )
    else:
        parts.extend(
            [
                "",
                "# 🏗️ PROJECT CONTEXT",
                _get_static_project_structure().strip(),
            ]
        )

    if include_health:
        parts.extend(
            [
                "",
                "## 📊 CURRENT SYSTEM STATUS",
                _get_system_health(),
            ]
        )

    if include_capabilities:
        parts.extend(
            [
                "",
                _get_capabilities().strip(),
            ]
        )

    # Add timestamp and final instructions
    parts.extend(
        [
            "",
            f"## ⏰ Session Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "# RESPONSE GUIDELINES",
            "- When asked about the project, provide specific, accurate information based on the real-time analysis above.",
            "- إذا سُئلت عن المشروع، قدم معلومات دقيقة ومحددة بناءً على التحليل الفعلي أعلاه.",
            "- If asked about issues, refer to the 'Current Issues' section.",
            "- If asked about strengths, refer to the 'Project Strengths' section.",
            "- Always be specific with file names, line counts, and technical details.",
        ]
    )

    return "\n".join(parts)


# =============================================================================
# LEGACY SUPPORT
# =============================================================================

# Keep the old constant for backward compatibility (generated once at import)
OVERMIND_SYSTEM_PROMPT = get_system_prompt()
