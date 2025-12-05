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
