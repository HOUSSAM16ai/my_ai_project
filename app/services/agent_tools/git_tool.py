"""
أداة تنفيذ أوامر Git.
======================

توفر إمكانية تنفيذ أوامر Git الشائعة بشكل آمن:
- status, log, diff, branch, commit, push, pull

المعايير:
- CS50 2025: توثيق عربي، صرامة في الأنواع
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# أوامر Git المسموحة
ALLOWED_GIT_COMMANDS = frozenset({
    "status", "log", "diff", "branch", "show", "blame",
    "fetch", "pull", "push", "commit", "add", "reset",
    "checkout", "merge", "rebase", "stash", "tag",
    "remote", "init", "clone", "config",
})


async def execute_git(
    subcommand: str,
    args: str = "",
    cwd: str | None = None,
    timeout: int = 30,
) -> dict[str, object]:
    """
    تنفيذ أمر Git.

    Args:
        subcommand: الأمر الفرعي (status, log, commit, etc.)
        args: الوسائط الإضافية
        cwd: مسار العمل (المستودع)
        timeout: المهلة الزمنية

    Returns:
        dict: {success, stdout, stderr, return_code, error}
    """
    subcommand = subcommand.strip().lower()
    
    logger.info(f"Git: Executing 'git {subcommand} {args}'")

    # 1. التحقق من صحة الأمر
    if subcommand not in ALLOWED_GIT_COMMANDS:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": f"Git subcommand '{subcommand}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_GIT_COMMANDS))}",
        }

    # 2. تحديد مسار العمل
    work_dir = Path(cwd) if cwd else Path.cwd()
    if not work_dir.exists():
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": f"Directory does not exist: {work_dir}",
        }

    # 3. التحقق من وجود Git repo
    git_dir = work_dir / ".git"
    if not git_dir.exists() and subcommand not in ("init", "clone"):
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": f"Not a git repository: {work_dir}",
        }

    # 4. بناء الأمر
    command = f"git {subcommand}"
    if args:
        command += f" {args}"

    # 5. تنفيذ الأمر
    try:
        result = await asyncio.wait_for(
            _run_git_command(command, work_dir),
            timeout=timeout,
        )
        return result

    except asyncio.TimeoutError:
        logger.warning(f"Git: Command timed out after {timeout}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": f"Git command timed out after {timeout} seconds",
        }

    except Exception as e:
        logger.error(f"Git: Unexpected error: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "error": str(e),
        }


async def _run_git_command(command: str, cwd: Path) -> dict[str, object]:
    """
    تشغيل أمر Git.
    """
    loop = asyncio.get_running_loop()

    def _execute():
        process = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return {
            "success": process.returncode == 0,
            "stdout": process.stdout[:10000],
            "stderr": process.stderr[:5000],
            "return_code": process.returncode,
            "error": None if process.returncode == 0 else process.stderr[:500],
        }

    return await loop.run_in_executor(None, _execute)


# أدوات مختصرة للأوامر الشائعة
async def git_status(cwd: str | None = None) -> dict[str, object]:
    """الحصول على حالة المستودع."""
    return await execute_git("status", "--short", cwd)


async def git_log(cwd: str | None = None, count: int = 10) -> dict[str, object]:
    """عرض سجل الـ commits."""
    return await execute_git("log", f"--oneline -n {count}", cwd)


async def git_diff(cwd: str | None = None, file: str = "") -> dict[str, object]:
    """عرض التغييرات."""
    return await execute_git("diff", file, cwd)


async def git_branch(cwd: str | None = None) -> dict[str, object]:
    """عرض الفروع."""
    return await execute_git("branch", "-a", cwd)


async def git_add(files: str = ".", cwd: str | None = None) -> dict[str, object]:
    """إضافة ملفات للـ staging."""
    return await execute_git("add", files, cwd)


async def git_commit(message: str, cwd: str | None = None) -> dict[str, object]:
    """إنشاء commit."""
    # تنظيف الرسالة من الأقواس
    safe_message = message.replace('"', '\\"')
    return await execute_git("commit", f'-m "{safe_message}"', cwd)


# تسجيل الأدوات
def register_git_tools(registry: dict) -> None:
    """
    تسجيل أدوات Git في سجل الأدوات.
    """
    registry["git"] = execute_git
    registry["git_status"] = git_status
    registry["git_log"] = git_log
    registry["git_diff"] = git_diff
    registry["git_branch"] = git_branch
    registry["git_add"] = git_add
    registry["git_commit"] = git_commit
    logger.info("Git tools registered successfully")
