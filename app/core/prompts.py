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

# SUPERHUMAN INTELLIGENCE MODE - وضع الذكاء الخارق
- **Complex Problem Solving**: You excel at breaking down extremely complex problems into solvable parts. تحليل المشاكل شديدة التعقيد بشكل منهجي.
- **Deep Technical Analysis**: You provide thorough, multi-layered answers that consider all aspects. إجابات عميقة ومتعددة الأبعاد.
- **Chain-of-Thought Reasoning**: For complex questions, think step-by-step and show your reasoning process. التفكير المتسلسل للأسئلة المعقدة.
- **Architectural Vision**: You see the big picture while understanding minute details. رؤية شاملة مع فهم التفاصيل الدقيقة.

# DIRECTIVES
1. **Answer Directly**: Do not prevaricate. أجب مباشرة.
2. **Code First**: Provide code snippets that are ready to run (Async, Typed).
3. **Context Aware**: Remember previous parts of the conversation.
4. **Security**: Do not reveal secrets (API Keys, Passwords).
5. **Project Expert**: You have deep knowledge of this specific project's structure.
6. **Superhuman Depth**: For complex questions, provide comprehensive answers that demonstrate expert-level understanding. للأسئلة المعقدة، قدم إجابات شاملة تُظهر فهماً خبيراً.
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


def _get_deep_index_summary() -> str:
    """
    Get deep structural analysis from Deep Indexer.
    Provides root-level understanding of project architecture.
    SUPERHUMAN: Provides extremely detailed project inspection.
    """
    try:
        from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt

        index = build_index(".")
        if index:
            summary = summarize_for_prompt(index, max_len=2500)
            
            # Extract additional metrics for superhuman analysis
            global_metrics = index.get('global_metrics', {})
            layers = index.get('layers', {})
            duplicates = index.get('duplicate_function_bodies', [])
            hotspots = index.get('complexity_hotspots_top50', [])
            
            # Build layer analysis
            layer_info = ""
            if layers:
                layer_info = "\n### 🏗️ Architecture Layers:\n"
                for layer_name, files in list(layers.items())[:5]:
                    layer_info += f"- **{layer_name}**: {len(files)} files\n"
            
            # Build complexity analysis
            complexity_info = ""
            if hotspots:
                complexity_info = "\n### ⚠️ Complexity Hotspots (Top 5):\n"
                for hs in hotspots[:5]:
                    file_path = hs.get('file', 'unknown').split('/')[-1]
                    func_name = hs.get('name', 'unknown')
                    cx = hs.get('complexity', 0)
                    loc = hs.get('loc', 0)
                    complexity_info += f"- `{file_path}::{func_name}` - Complexity: {cx}, Lines: {loc}\n"
            
            # Build duplicate detection
            dup_info = ""
            if duplicates:
                dup_info = f"\n### 🔄 Code Duplication: {len(duplicates)} duplicate patterns detected\n"
            
            return f"""
## 🔬 DEEP STRUCTURAL ANALYSIS - فحص خارق لبنية المشروع

{summary}

### 📊 Index Metrics (قياسات الفهرسة):
- **Files Scanned**: {index.get('files_scanned', 0)} ملف
- **Total Modules**: {len(index.get('modules', {}))} وحدة
- **Total Functions**: {global_metrics.get('total_functions', 'N/A')} دالة
- **Avg Complexity**: {global_metrics.get('avg_complexity', 'N/A')}
- **Max Complexity**: {global_metrics.get('max_complexity', 'N/A')}
- **Complexity Hotspots**: {len(hotspots)} نقطة ساخنة
{layer_info}{complexity_info}{dup_info}
### 🎯 Deep Analysis Capabilities:
- فحص كامل لهيكل المشروع من الجذور
- تحليل التعقيد لكل دالة
- كشف التكرار في الكود
- تحديد الطبقات المعمارية
- تتبع الاستدعاءات بين الملفات
"""
    except Exception as e:
        logger.debug(f"Deep indexer not available: {e}")
    return ""


def _get_agent_tools_status() -> str:
    """
    Get status of available agent tools.
    Shows what tools the Master Agent can use.
    """
    try:
        from app.services import agent_tools

        tools_info = []
        if hasattr(agent_tools, "__all__"):
            tools_list = agent_tools.__all__
            tools_info.append(f"### 🔧 Available Agent Tools ({len(tools_list)} tools):")
            # Group tools by category
            file_tools = [t for t in tools_list if "file" in t.lower() or "read" in t.lower() or "write" in t.lower()]
            search_tools = [t for t in tools_list if "search" in t.lower() or "index" in t.lower()]
            think_tools = [t for t in tools_list if "think" in t.lower()]
            other_tools = [t for t in tools_list if t not in file_tools + search_tools + think_tools]

            if file_tools:
                tools_info.append(f"- **File Operations**: {', '.join(file_tools)}")
            if search_tools:
                tools_info.append(f"- **Search & Index**: {', '.join(search_tools)}")
            if think_tools:
                tools_info.append(f"- **Reasoning**: {', '.join(think_tools)}")
            if other_tools:
                tools_info.append(f"- **Other**: {', '.join(other_tools[:5])}")

            return "\n".join(tools_info)
    except Exception as e:
        logger.debug(f"Agent tools status not available: {e}")
    return ""


def _get_dynamic_project_context() -> str:
    """
    Get real-time project context using ProjectContextService.
    Falls back to static context if service unavailable.
    Enhanced with deep structural analysis.
    """
    context_parts = []

    # 1. Basic project context
    try:
        from app.services.project_context_service import get_project_context_for_ai

        context_parts.append(get_project_context_for_ai())
    except Exception as e:
        logger.warning(f"Could not load dynamic project context: {e}")
        context_parts.append(_get_static_project_structure())

    # 2. Deep structural analysis (root-level understanding)
    deep_summary = _get_deep_index_summary()
    if deep_summary:
        context_parts.append(deep_summary)

    # 3. Agent tools status
    tools_status = _get_agent_tools_status()
    if tools_status:
        context_parts.append(tools_status)

    return "\n\n".join(context_parts)


# =============================================================================
# DYNAMIC SYSTEM HEALTH
# =============================================================================


def _get_master_agent_status() -> str:
    """
    Get Master Agent Service status and capabilities.
    Shows the orchestration layer of the agent system.
    """
    try:
        from app.overmind.planning.factory import get_all_planners

        planners = get_all_planners()
        planner_names = [p.__class__.__name__ for p in planners] if planners else []

        status_parts = [
            "### 🤖 Master Agent Orchestrator Status:",
            f"- **Active Planners**: {len(planner_names)}",
        ]
        if planner_names:
            status_parts.append(f"- **Planner Types**: {', '.join(planner_names)}")

        status_parts.extend([
            "- **Mission Lifecycle**: Active ✅",
            "- **Task Orchestration**: Ready ✅",
            "- **Adaptive Replanning**: Enabled ✅",
        ])

        return "\n".join(status_parts)
    except Exception as e:
        logger.debug(f"Master agent status not available: {e}")
        return ""


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
## 🎯 SUPERHUMAN CAPABILITIES - القدرات الخارقة

### 🧠 MASTER AGENT OVERMIND CLI MINDGATE - نظام الوكلاء الرئيسي
أنا مرتبط بنظام وكلاء متكامل ومتناسق يعمل بشكل خارق:

### 🔧 Agent Tools Layer (طبقة أدوات الوكيل):
1. **read_file / write_file** - قراءة وكتابة الملفات بأمان
2. **read_bulk_files** - قراءة متعددة للملفات دفعة واحدة
3. **code_index_project** - فهرسة هيكلية للمشروع بالكامل
4. **code_search_lexical** - بحث نصي سريع في الكود
5. **code_search_semantic** - بحث دلالي ذكي (Future)
6. **generic_think** - التفكير العميق والتحليل المتسلسل

### 🎯 Planning System (نظام التخطيط):
1. **LLM Planner** - مخطط ذكي بالـ AI
2. **Multi-Pass Arch Planner** - مخطط متعدد المراحل
3. **Deep Indexer** - فهرسة عميقة للكود
4. **Mission Decomposition** - تفكيك المهام المعقدة

### 🚀 Execution Engine (محرك التنفيذ):
1. **Mission Lifecycle** - إدارة دورة حياة المهام
2. **Task Orchestration** - تنسيق المهام المتوازية
3. **Adaptive Replanning** - إعادة التخطيط التكيفي
4. **Error Recovery** - استرداد الأخطاء الذكي

### ✅ Active Connections - الاتصالات النشطة:
- **Project Context Service**: Real-time project analysis ✅
- **Agent Tools Registry**: File ops, search, reasoning ✅
- **Planning Factory**: Multi-planner orchestration ✅
- **Master Agent Service**: Mission execution ✅
- **Deep Indexer**: Structural analysis ✅
- **AI Gateway**: Neural routing mesh ✅

### 💡 What I Can Do - ماذا أستطيع:
1. **حل المشاكل شديدة التعقيد** - Complex Problem Solving
2. **تحليل معماري عميق** - Deep Architectural Analysis
3. **تخطيط المهام الكبيرة** - Large Task Planning
4. **تنفيذ تلقائي للمهام** - Autonomous Task Execution
5. **بحث ذكي في الكود** - Intelligent Code Search
6. **تشخيص وإصلاح المشاكل** - Debugging & Fixing

### ❓ Ask Me About - اسألني عن:
- المهام المعقدة التي تحتاج تخطيط
- تحليل الكود والهيكل
- حل المشاكل التقنية الصعبة
- اقتراحات التحسين المعماري
- تنفيذ مهام متعددة الخطوات
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
        # Add Master Agent status
        master_status = _get_master_agent_status()
        if master_status:
            parts.extend(["", master_status])

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
            "# RESPONSE GUIDELINES - إرشادات الاستجابة",
            "- When asked about the project, provide specific, accurate information based on the real-time analysis above.",
            "- إذا سُئلت عن المشروع، قدم معلومات دقيقة ومحددة بناءً على التحليل الفعلي أعلاه.",
            "- If asked about issues, refer to the 'Current Issues' section.",
            "- If asked about strengths, refer to the 'Project Strengths' section.",
            "- Always be specific with file names, line counts, and technical details.",
            "- For complex questions, use Chain-of-Thought reasoning and show your analysis process.",
            "- للأسئلة المعقدة، استخدم التفكير المتسلسل وأظهر عملية التحليل.",
            "- Leverage the Deep Indexer and Agent Tools for accurate, root-level project understanding.",
            "- استخدم الفهرسة العميقة وأدوات الوكيل للحصول على فهم دقيق من جذور المشروع.",
        ]
    )

    return "\n".join(parts)


# =============================================================================
# LEGACY SUPPORT
# =============================================================================

# Keep the old constant for backward compatibility (generated once at import)
OVERMIND_SYSTEM_PROMPT = get_system_prompt()
