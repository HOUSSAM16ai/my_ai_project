
import os
import re
import math
from . import config

# --------------------------------------------------------------------------------------
# Patterns & Sets
# --------------------------------------------------------------------------------------
FILENAME_PATTERNS = [
    r"\bfile\s+named\s+([A-Za-z0-9_\-./]+)",
    r"\bfiles?\s+named\s+([A-Za-z0-9_\-./,\s]+)",
    r"\bsave\s+(?:it\s+)?as\s+([A-Za-z0-9_\-./]+)",
    r"\bwrite\s+(?:to|into)\s+([A-Za-z0-9_\-./]+)",
    r"\boutput\s+to\s+([A-Za-z0-9_\-./]+)",
    r"\bdeliver(?:able)?\s+([A-Za-z0-9_\-./]+)",
    r"ملف\s+باسم\s+([A-Za-z0-9_\-./]+)",
    r"ملفات\s+باسم\s+([A-Za-z0-9_\-./,\s]+)",
    r"احفظه\s+في\s+([A-Za-z0-9_\-./]+)",
    r"اكتب\s+في\s+([A-Za-z0-9_\-./]+)",
    r"الناتج\s+في\s+([A-Za-z0-9_\-./]+)",
    r"مخرجات\s+في\s+([A-Za-z0-9_\-./]+)",
]
SEP_SPLIT = re.compile(r"\s*(?:,|و|and)\s*", re.IGNORECASE)
LINE_REQ = re.compile(r"(\d{2,9})\s*(?:lines?|أسطر|سطر)", re.IGNORECASE)
HUGE_TERMS = [
    "very large",
    "huge",
    "massive",
    "enormous",
    "gigantic",
    "immense",
    "ضخم",
    "هائل",
    "كبير جدا",
    "مليونية",
    "كثيرة جدا",
    "مليونية",
]

SECTION_HINTS_AR = [
    "مقدمة",
    "نظرة عامة",
    "تحليل",
    "معمارية",
    "تدفق البيانات",
    "مكونات",
    "تفاصيل",
    "مخاطر",
    "تحسينات",
    "توصيات",
    "خاتمة",
    "ملاحق",
]
SECTION_HINTS_EN = [
    "Introduction",
    "Overview",
    "Analysis",
    "Architecture",
    "Data Flow",
    "Components",
    "Details",
    "Risks",
    "Improvements",
    "Recommendations",
    "Conclusion",
    "Appendices",
]

CODE_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".rb",
    ".rs",
    ".php",
    ".sh",
    ".ps1",
    ".sql",
}
DATA_EXTS = {".json", ".yml", ".yaml", ".ini", ".cfg", ".toml", ".csv", ".xml"}
DOC_EXTS = {".md", ".rst", ".txt", ".log", ".html", ".adoc"}


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _has_arabic(s: str) -> bool:
    return any("\u0600" <= c <= "\u06ff" for c in s)


def _detect_lang(obj: str) -> str:
    if config.FORCE_AR:
        return "ar"
    low = obj.lower()
    if _has_arabic(obj) or "arabic" in low:
        return "ar"
    if "english" in low:
        return "en"
    return config.LANG_FALLBACK if config.LANG_FALLBACK in ("ar", "en") else "ar"


def _normalize_filename(fn: str) -> str:
    fn = fn.strip()
    if config.SMART_FN:
        fn = fn.replace("\\", "/").replace("//", "/")
        fn = re.sub(r"[^A-Za-z0-9_\-./]", "_", fn)
    if not config.ALLOW_SUBDIRS and "/" in fn:
        fn = fn.split("/")[-1]
    return fn


def _ensure_ext(fn: str) -> str:
    return fn if "." in fn else fn + config.DEFAULT_EXT


def extract_filenames(obj: str) -> list[str]:
    norm = " ".join(obj.split())
    out = []
    for pat in FILENAME_PATTERNS:
        for m in re.finditer(pat, norm, re.IGNORECASE):
            raw = m.group(1)
            if not raw:
                continue
            for p in SEP_SPLIT.split(raw):
                p = _normalize_filename(p)
                if not p:
                    continue
                if "." not in p:
                    p = _ensure_ext(p)
                if p.lower() not in [x.lower() for x in out]:
                    out.append(p)
                if len(out) >= config.MAX_FILES:
                    break
        if len(out) >= config.MAX_FILES:
            break
    if not out:
        guess = re.findall(r"\b([A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+))\b", norm)
        for g in guess:
            g = _normalize_filename(g)
            if g.lower() not in [x.lower() for x in out]:
                out.append(g)
            if len(out) >= config.MAX_FILES:
                break
    if not out:
        out = ["output" + config.DEFAULT_EXT]
    return out[:config.MAX_FILES]


def extract_requested_lines(obj: str) -> int | None:
    mx = None
    for m in LINE_REQ.finditer(obj):
        try:
            val = int(m.group(1))
            if mx is None or val > mx:
                mx = val
        except Exception:
            pass
    if any(t in obj.lower() for t in HUGE_TERMS):
        mx = config.CHUNK_SIZE_HINT * 10 if mx is None else int(mx * 1.5)
    if mx and mx > config.HARD_LINE_CAP:
        mx = config.HARD_LINE_CAP
    return mx


def compute_chunk_plan(requested: int | None) -> tuple[int, int]:
    if not requested:
        requested = config.CHUNK_SIZE_HINT * 2
    if requested <= config.FAST_SINGLE_THRESH:
        return 1, requested
    chunk_count = math.ceil(requested / config.CHUNK_SIZE_HINT)
    if chunk_count > config.MAX_CHUNKS:
        chunk_count = config.MAX_CHUNKS
    per_chunk = max(80, math.ceil(requested / chunk_count))
    return chunk_count, per_chunk


def infer_sections(obj: str, lang: str) -> list[str]:
    if not config.SECTION_INFER:
        return []
    pat = re.compile(
        r"(?:sections?|أقسام|ضع\s+أقسام|include\s+sections?)\s*[:：]\s*(.+)", re.IGNORECASE
    )
    m = pat.search(obj)
    if m:
        tail = m.group(1)
        parts = re.split(r"[;,،]|(?:\band\b)|(?:\sو\s)", tail)
        cleaned = [p.strip(" .\t") for p in parts if p.strip()]
        return cleaned[:25]
    return []


def file_type(fn: str) -> str:
    ext = os.path.splitext(fn)[1].lower()
    if ext in CODE_EXTS:
        return "code"
    if ext in DATA_EXTS:
        return "data"
    if ext in DOC_EXTS:
        return "doc"
    return "generic"


def code_hint(ftype: str, lang: str) -> str:
    if not config.CODE_HINTS:
        return ""
    if ftype == "code":
        return (
            "أضف أمثلة كود وتعليقات عميقة.\n"
            if lang == "ar"
            else "Add deep code samples & commentary.\n"
        )
    if ftype == "data":
        return (
            "أضف سجلات نموذجية وشرح الحقول.\n"
            if lang == "ar"
            else "Provide sample records & field descriptions.\n"
        )
    return ""


def _truncate(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else s[:max_chars] + "\n[TRUNCATED]"


def _tid(i: int) -> str:
    return f"t{i:02d}"
