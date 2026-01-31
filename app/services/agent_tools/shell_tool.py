"""
أداة تنفيذ أوامر Shell.
========================

توفر إمكانية تنفيذ أوامر النظام بشكل آمن مع:
- حدود زمنية (timeout)
- تحديد المسار الآمن
- تسجيل الأوامر

المعايير:
- CS50 2025: توثيق عربي، صرامة في الأنواع
- SICP: Abstraction Barriers
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# قائمة الأوامر المحظورة للأمان
BLOCKED_COMMANDS = frozenset(
    {
        "rm -rf /",
        "rm -rf /*",
        "format",
        "del /f /s /q",
        "shutdown",
        "reboot",
        ":(){:|:&};:",  # fork bomb
    }
)

# قائمة الأوامر المسموحة بالكامل
ALLOWED_COMMANDS = frozenset(
    {
        "ls",
        "dir",
        "pwd",
        "cd",
        "cat",
        "head",
        "tail",
        "grep",
        "find",
        "wc",
        "echo",
        "python",
        "pip",
        "pytest",
        "npm",
        "node",
        "git",
        "curl",
        "wget",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "chmod",
        "chown",
        "type",
        "more",
        "less",
    }
)


async def execute_shell(
    command: str,
    cwd: str | None = None,
    timeout: int = 30,
    check_safety: bool = True,
) -> dict[str, object]:
    """
    تنفيذ أمر shell بشكل آمن.

    Args:
        command: الأمر المراد تنفيذه
        cwd: مسار العمل (اختياري)
        timeout: المهلة الزمنية بالثواني
        check_safety: التحقق من أمان الأمر

    Returns:
        dict: {success, stdout, stderr, return_code, error}
    """
    logger.info(f"Shell: Executing command: {command[:100]}...")

    # 1. التحقق من الأمان
    if check_safety:
        safety_result = _check_command_safety(command)
        if not safety_result["safe"]:
            logger.warning(f"Shell: Blocked unsafe command: {command}")
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "return_code": -1,
                "error": safety_result["reason"],
            }

    # 2. تحديد مسار العمل
    work_dir = Path(cwd) if cwd else Path.cwd()
    if not work_dir.exists():
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": f"Working directory does not exist: {work_dir}",
        }

    # 3. تنفيذ الأمر
    try:
        return await asyncio.wait_for(
            _run_command(command, work_dir),
            timeout=timeout,
        )

    except TimeoutError:
        logger.warning(f"Shell: Command timed out after {timeout}s: {command}")
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": f"Command timed out after {timeout} seconds",
        }

    except Exception as e:
        logger.error(f"Shell: Unexpected error: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": str(e),
        }


async def _run_command(command: str, cwd: Path) -> dict[str, object]:
    """
    تشغيل الأمر في subprocess.

    Args:
        command: الأمر
        cwd: مسار العمل

    Returns:
        dict: نتيجة التنفيذ
    """
    loop = asyncio.get_running_loop()

    def _execute():
        # استخدام shell=True للسماح بالأوامر المركبة
        # لكن مع التحقق من الأمان مسبقاً
        process = subprocess.run(
            command,
            shell=True,
            check=False,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60,  # حد أقصى داخلي
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return {
            "success": process.returncode == 0,
            "stdout": process.stdout[:10000],  # حد 10KB
            "stderr": process.stderr[:5000],  # حد 5KB
            "return_code": process.returncode,
            "error": None if process.returncode == 0 else process.stderr[:500],
        }

    return await loop.run_in_executor(None, _execute)


def _check_command_safety(command: str) -> dict[str, object]:
    """
    التحقق من أمان الأمر.

    Args:
        command: الأمر المراد فحصه

    Returns:
        dict: {safe: bool, reason: str}
    """
    command_lower = command.lower().strip()

    # 1. فحص الأوامر المحظورة
    for blocked in BLOCKED_COMMANDS:
        if blocked in command_lower:
            return {"safe": False, "reason": f"Blocked dangerous command pattern: {blocked}"}

    # 2. فحص الأنماط الخطيرة
    dangerous_patterns = [
        "rm -rf",
        "rm -r /",
        "del /s /q",
        "> /dev/",
        "mkfs",
        "dd if=",
        ":(){",
        "chmod 777 /",
        "curl | sh",
        "wget | sh",
        "eval(",
        "exec(",
    ]

    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return {"safe": False, "reason": f"Detected dangerous pattern: {pattern}"}

    # 3. التحقق من الحقن
    if ";" in command and ("rm " in command_lower or "del " in command_lower):
        return {"safe": False, "reason": "Command chaining with delete operations is not allowed"}

    return {"safe": True, "reason": "Command passed safety checks"}


# تسجيل الأداة في السجل
def register_shell_tool(registry: dict) -> None:
    """
    تسجيل أداة shell في سجل الأدوات.

    Args:
        registry: سجل الأدوات
    """
    registry["shell"] = execute_shell
    registry["execute_shell"] = execute_shell
    registry["run_command"] = execute_shell
    logger.info("Shell tool registered successfully")
