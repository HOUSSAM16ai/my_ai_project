import ast
import hashlib
import os

# Assuming these imports exist in the original context, we need to locate them.
# The original file used: from ._layer_detection import detect_layer; from ._tag_detection import categorize_code
# Since we are in a subdirectory now, we need to adjust imports.
# The files _layer_detection.py and _tag_detection.py are in app/overmind/planning/.
# So we import from .._layer_detection
from .._layer_detection import detect_layer
from .._tag_detection import categorize_code
from .config import CONFIG


def read_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: str) -> str:
    try:
        st = os.stat(path)
        # Fast: mtime + size + sha256 partial (first 64KB)
        with open(path, "rb") as f:
            head = f.read(64 * 1024)
        composite = f"{path}:{st.st_mtime_ns}:{st.st_size}:{hashlib.sha256(head).hexdigest()}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()
    except Exception:
        return "deadbeef"


def hash_norm_function(code: str, prefix: int) -> str:
    """
    Extremely simplified normalization:
      - Remove comments
      - Remove empty lines
      - Remove repeated spaces
      - Limit to first 'prefix' chars of sha256
    """
    lines = []
    skip_doc = False
    doc_open = None
    for ln in code.splitlines():
        # Strip inline comments
        if "#" in ln:
            ln = ln.split("#", 1)[0]

        stripped = ln.strip()
        if not stripped:
            continue

        # Primitive multiline string removal (Docstring)
        if stripped.startswith(('"""', "'''")):
            marker = stripped[:3]
            if stripped.count(marker) == 1 and not stripped.endswith(marker):
                # Started multiline docstring
                skip_doc = True
                doc_open = marker
                continue
            if stripped.count(marker) >= 2:
                # Single line docstring - ignore
                continue
        if skip_doc:
            if doc_open and doc_open in stripped:
                skip_doc = False
            continue
        lines.append(stripped)
    norm = " ".join(lines)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:prefix]


def categorize(code: str) -> list[str]:
    """
    Categorize code by detecting technology tags.
    """
    return categorize_code(code)


def layer_for_path(path: str) -> str | None:
    """
    Detect architectural layer.
    """
    return detect_layer(path, CONFIG["LAYER_HEURISTICS"])


def service_candidate(path: str, code: str) -> bool:
    if not CONFIG["DETECT_SERVICES"]:
        return False
    lower = code.lower()
    # Simplified criteria: file in services/ or contains FastAPI/Blueprint/Router construction
    if "services" in path or "service" in path:
        return True
    return bool(any(x in lower for x in ("fastapi(", "flask(", "blueprint(", "apirouter(")))


def detect_entrypoint(code: str, lines: list[str]) -> bool:
    if "__name__" in code and "__main__" in code:
        # Cheap pattern
        for ln in lines:
            if "if __name__" in ln and "__main__" in ln:
                return True
    return False


def parse_ast_safely(code: str) -> ast.AST | str:
    # Returns AST or error string
    try:
        return ast.parse(code)
    except Exception as e:
        return f"parse_error:{e}"
