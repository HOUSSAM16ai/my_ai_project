# app/services/agent_tools/domain/fs.py
# =================================================================================================
# FILE SYSTEM TOOLS – THE HANDS OF THE AGENT (أدوات نظام الملفات)
# Version: 5.0.0-secure-optimized
# =================================================================================================

import asyncio
import os

from app.services.agent_tools.new_core import tool

# Safety Configuration: حدود المشروع الآمنة
# نمنع الوكيل من العبث بملفات النظام الحساسة
PROJECT_ROOT = os.path.abspath(os.getenv("AGENT_TOOLS_PROJECT_ROOT", "/app"))

def _safe_path(path: str) -> str:
    """
    التحقق الأمني من المسار (Security Check).
    يمنع هجمات Directory Traversal (مثل ../../../etc/passwd).
    """
    # تسوية المسار وحذف النقاط الزائدة
    target = os.path.abspath(os.path.join(PROJECT_ROOT, path))

    # التأكد أن المسار لا يزال داخل حدود المشروع
    if not target.startswith(PROJECT_ROOT):
        raise PermissionError(f"Access denied: Path '{path}' is outside project root. Stay safe!")

    return target

# --- Async File Helper (مساعد الملفات غير المتزامن) ---
# لتجنب تجميد النظام أثناء قراءة الملفات الكبيرة

class AsyncFileContext:
    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
        self.file = None

    async def __aenter__(self):
        loop = asyncio.get_running_loop()
        self.file = await loop.run_in_executor(None, open, self.path, self.mode)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.file.close)

    async def read(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.file.read)

    async def write(self, data):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.file.write, data)

def asyncio_open(path: str, mode: str):
    return AsyncFileContext(path, mode)

# --- The Tools (الأدوات) ---

@tool(
    name="read_file",
    description="Reads the content of a file (قراءة محتوى ملف).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."}
        },
        "required": ["path"]
    }
)
async def read_file(path: str) -> str:
    """
    قراءة ملف بأمان وسرعة.
    """
    safe_target = _safe_path(path)
    if not os.path.exists(safe_target):
        raise FileNotFoundError(f"File not found: {path}")

    async with asyncio_open(safe_target, "r") as f:
        content = await f.read()
    return content

@tool(
    name="write_file",
    description="Writes content to a file (كتابة أو إنشاء ملف).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."},
            "content": {"type": "string", "description": "Content to write."}
        },
        "required": ["path", "content"]
    }
)
async def write_file(path: str, content: str) -> str:
    """
    كتابة ملف بأمان (ينشئ المجلدات تلقائياً).
    """
    safe_target = _safe_path(path)

    # إنشاء المجلدات إذا لم تكن موجودة
    os.makedirs(os.path.dirname(safe_target), exist_ok=True)

    async with asyncio_open(safe_target, "w") as f:
        await f.write(content)

    return f"File written successfully: {path}"

@tool(
    name="list_files",
    description="Lists files in a directory (عرض الملفات).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (default: .)."}
        }
    }
)
async def list_files(path: str = ".") -> list[str]:
    """
    عرض قائمة الملفات بشكل متكرر (Recursive).
    """
    safe_target = _safe_path(path)

    if not os.path.isdir(safe_target):
        raise NotADirectoryError(f"Not a directory: {path}")

    loop = asyncio.get_running_loop()

    def _walk():
        result = []
        # نستخدم os.walk للتجول داخل المجلدات الفرعية
        for root, _, filenames in os.walk(safe_target):
            # نتجاهل مجلدات git و cache لتسريع العملية
            if ".git" in root or "__pycache__" in root:
                continue

            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, safe_target)
                result.append(rel_path)

                # حماية من الانفجار في حالة المجلدات العملاقة
                if len(result) > 2000:
                    return result
        return result

    files = await loop.run_in_executor(None, _walk)
    return files
