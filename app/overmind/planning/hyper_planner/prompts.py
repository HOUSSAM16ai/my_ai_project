from .utils import _truncate, code_hint


# --------------------------------------------------------------------------------------
# Prompt Builders
# --------------------------------------------------------------------------------------
def build_role_prompt(
    files: list[str], objective: str, lang: str, struct_ref: str | None = None
) -> str:
    listing = ", ".join(files)
    struct_block = f"\nSTRUCT_CONTEXT:\n{struct_ref}\n" if struct_ref else ""
    if lang == "ar":
        return (
            f"الهدف:\n{objective}\nالملفات: {listing}{struct_block}"
            "حدد لكل ملف دوراً فريداً بدون تداخل. أعد JSON: "
            "[{filename,focus,outline_points,rationale,risks,potential_extensions}]."
        )
    return (
        f"Objective:\n{objective}\nFiles: {listing}{struct_block}"
        "Assign each file a distinct role (no overlap). Return JSON: "
        "[{filename,focus,outline_points,rationale,risks,potential_extensions}]."
    )


def build_section_prompt(
    objective: str, draft_sections: list[str], lang: str, struct_ref: str | None = None
) -> str:
    listing = "\n".join(f"- {s}" for s in draft_sections)
    struct_block = f"\nSTRUCT_CONTEXT:\n{struct_ref}\n" if struct_ref else ""
    if lang == "ar":
        return (
            f"الهدف:\n{objective}\nالأقسام المقترحة:\n{listing}{struct_block}"
            "حسّن وأعد JSON: [{order,section_title,notes,priority}]."
        )
    return (
        f"Objective:\n{objective}\nDraft Sections:\n{listing}{struct_block}"
        "Refine -> JSON [{order,section_title,notes,priority}]."
    )


def build_chunk_prompt(
    objective: str,
    fname: str,
    role_id: str | None,
    section_id: str | None,
    cidx: int,
    ctotal: int,
    target_lines: int,
    lang: str,
    ftype: str,
    struct_placeholder: str | None = None,
    inline_struct: str = "",
) -> str:
    role_ref = f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    sect_ref = f"{{{{{section_id}.answer}}}}" if section_id else "(no-sections)"
    if struct_placeholder:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{{{{{struct_placeholder}.answer}}}}"
    elif inline_struct:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{_truncate(inline_struct, 800)}"
    else:
        struct_ref = ""
    if lang == "ar":
        header = (
            f"الهدف:\n{objective}\nالملف:{fname}\nالدور:{role_ref}\nالأقسام:{sect_ref}{struct_ref}\n"
            f"جزء {cidx}/{ctotal} (~{target_lines} سطر)\n"
        )
        guide = (
            "- تابع تدريجياً.\n- لا خاتمة قبل الجزء الأخير.\n- أضف قوائم، أمثلة، مخاطر، تحسينات.\n"
            "- لا تكرر المقدمة كاملة.\n"
        )
        return header + guide + code_hint(ftype, lang)
    header = (
        f"Objective:\n{objective}\nFile:{fname}\nRole:{role_ref}\nSections:{sect_ref}{struct_ref}\n"
        f"Chunk {cidx}/{ctotal} (~{target_lines} lines)\n"
    )
    guide = (
        "- Maintain flow; no early finalization.\n- Add lists/examples/risks/refactor ideas.\n"
        "- Avoid full intro repetition.\n"
    )
    return header + guide + code_hint(ftype, lang)


def build_final_wrap_prompt(
    objective: str,
    fname: str,
    role_id: str | None,
    lang: str,
    struct_placeholder: str | None = None,
    inline_struct: str = "",
) -> str:
    role_ref = f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    if struct_placeholder:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{{{{{struct_placeholder}.answer}}}}"
    elif inline_struct:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{_truncate(inline_struct, 800)}"
    else:
        struct_ref = ""
    if lang == "ar":
        return (
            f"الهدف:\n{objective}\nالملف:{fname}{struct_ref}\n"
            f"اكتب خلاصة تنفيذية موجزة (<=200 سطر) مبنية على {role_ref} وتتضمن توصيات عملية مرتبة."
        )
    return (
        f"Objective:\n{objective}\nFile:{fname}{struct_ref}\n"
        f"Produce an executive wrap (<=200 lines) leveraging {role_ref} + prioritized recommendations."
    )


# --- Migrated Prompts from core.py ---

def semantic_analysis_prompt(lang: str, sem_source: str, max_bytes: int) -> str:
    if lang == "ar":
        return (
            "حلل الملخص البنيوي وأعد JSON:\n"
            "{layers:[...],services:[...],infra:[...],utilities:[...],hotspots:[...],duplicates:[...],"
            "refactor_opportunities:[{item,impact,effort}],risks:[{issue,likelihood,impact}],patterns:[...]}\n\n"
            f"{_truncate(sem_source, max_bytes)}"
        )
    return (
        "Analyze structural summary -> JSON schema:\n"
        "{layers:[...],services:[...],infra:[...],utilities:[...],hotspots:[...],duplicates:[...],"
        "refactor_opportunities:[{item,impact,effort}],risks:[{issue,likelihood,impact}],patterns:[...]}\n\n"
        f"{_truncate(sem_source, max_bytes)}"
    )

def global_code_summary_prompt(lang: str, refs: str, max_bytes: int) -> str:
    if lang == "ar":
        return (
            "لخص هذه الملفات إلى خريطة وحدات/خدمات/بنية/وظائف حرجة/تكرارات محتملة. "
            "أعد JSON: {modules:[...],services:[...],infra:[...],utilities:[...],"
            "notable_functions:[...],potential_containers:[...],global_risks:[...]}.\n"
            + _truncate(refs, max_bytes)
        )
    return (
        "Summarize files into repository map (modules/services/layers/critical funcs/duplicate hints). "
        "Return JSON: {modules:[...],services:[...],infra:[...],utilities:[...],"
        "notable_functions:[...],potential_containers:[...],global_risks:[...]}.\n"
        + _truncate(refs, max_bytes)
    )

def artifact_index_prompt(lang: str) -> str:
    if lang == "ar":
        return "أنشئ فهرساً موجزاً لكل ملف (سطران: التركيز والاستخدام)."
    return "Create concise artifact index (2 lines per file: focus & usage)."

def deep_arch_report_prompt(lang: str) -> str:
    if lang == "ar":
        return (
            "حلل بيانات الفهرس (JSON + ملخص) وقدم تقرير معمارية متقدم "
            "(طبقات، خدمات، تبعيات، نقاط ساخنة، تكرار، أولويات refactor، مخاطر، فرص تحسين). "
            "Markdown منظم مختصر."
        )
    return (
        "Analyze structural index (JSON + summary) → advanced architecture report "
        "(layers, services, dependencies, hotspots, duplicates, refactor priorities, risks, improvements). "
        "Return concise structured Markdown."
    )

def comprehensive_analysis_prompt(lang: str) -> str:
    if lang == "ar":
        return """حلل المشروع بشكل شامل وقدم تقرير واحد متكامل يتضمن:

- طبقات النظام والخدمات (الحاويات الثلاث: db, web, ai_service)
- التبعيات والعلاقات بين المكونات
- النقاط الساخنة والمناطق الحرجة في الكود

- ملخص الملفات الرئيسية ووظائفها
- الفئات والوظائف المهمة
- نقاط الدخول والواجهات البرمجية

- التكرار في الكود وفرص التحسين
- فرص إعادة الهيكلة والتنظيم
- المخاطر المحتملة ونقاط الضعف

- أولويات التحسين والتطوير
- الخطوات التالية المقترحة
- أفضل الممارسات للصيانة

قدم تحليل عميق ومنظم بذكاء خارق في ملف واحد شامل."""
    return """Analyze the project comprehensively and provide one integrated report including:

- System layers and services (three containers: db, web, ai_service)
- Dependencies and relationships between components
- Hotspots and critical areas in the code

- Summary of key files and their functions
- Important classes and functions
- Entry points and APIs

- Code duplication and improvement opportunities
- Refactoring and reorganization opportunities
- Potential risks and weaknesses

- Improvement and development priorities
- Suggested next steps
- Best practices for maintenance

Provide deep, organized analysis with superhuman intelligence in one comprehensive file."""
