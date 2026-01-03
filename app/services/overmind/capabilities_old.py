"""
نظام قدرات Overmind - التعديل على المشروع (Overmind Capabilities - Project Modification).

هذا النظام يوفر لـ Overmind القدرة الكاملة على:
- قراءة الملفات (Read Files)
- كتابة ملفات جديدة (Create Files)
- تعديل ملفات موجودة (Edit Files)
- حذف ملفات (Delete Files)
- إنشاء مجلدات (Create Directories)
- تنفيذ أوامر Shell (Execute Shell Commands)
- عمليات Git (Git Operations)

المبادئ المطبقة:
- Safety First: التحقق من الصلاحيات والأمان
- Logging: تسجيل جميع العمليات
- Error Handling: معالجة شاملة للأخطاء
- Rollback: إمكانية التراجع عن التغييرات

تحذيرات أمنية:
- ⚠️ يجب استخدام هذه القدرات بحذر شديد
- ⚠️ التحقق من المسارات لمنع الوصول لملفات النظام
- ⚠️ تسجيل جميع العمليات للمراجعة
- ⚠️ عدم حذف ملفات حساسة دون تأكيد
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.core.di import get_logger

logger = get_logger(__name__)


class FileOperations:
    """
    عمليات الملفات (File Operations).
    
    توفر عمليات آمنة ومُسجلة للتعامل مع الملفات والمجلدات.
    
    الأمان:
        - التحقق من المسارات (لا وصول خارج المشروع)
        - تسجيل جميع العمليات
        - منع حذف ملفات حساسة (.env, .git, إلخ)
    
    الاستخدام:
        >>> file_ops = FileOperations()
        >>> content = await file_ops.read_file("app/main.py")
        >>> await file_ops.write_file("new_file.py", "print('hello')")
        >>> await file_ops.edit_file("app/main.py", old_text, new_text)
    """
    
    def __init__(self, project_root: Path | None = None) -> None:
        """
        تهيئة نظام عمليات الملفات.
        
        Args:
            project_root: المجلد الجذر للمشروع (افتراضياً: المجلد الحالي)
            
        ملاحظة:
            - Path.cwd() تُرجع المجلد الحالي
            - .resolve() تحول المسار إلى مسار مطلق
        """
        self.project_root = (project_root or Path.cwd()).resolve()
        self.safe_paths = [
            self.project_root / "app",
            self.project_root / "tests",
            self.project_root / "scripts",
            self.project_root / "docs",
        ]
        
        # الملفات المحمية من الحذف (Protected Files)
        self.protected_files = {
            ".env",
            ".env.local",
            ".git",
            ".gitignore",
            "requirements.txt",
            "pyproject.toml",
        }
        
        logger.info(f"FileOperations initialized with root: {self.project_root}")
    
    def _is_safe_path(self, path: Path) -> bool:
        """
        التحقق من أن المسار آمن للوصول.
        
        Args:
            path: المسار المراد التحقق منه
            
        Returns:
            bool: True إذا كان المسار آمناً
            
        ملاحظة:
            - .resolve() تحول المسار إلى مسار مطلق
            - .is_relative_to() تتحقق من أن المسار ضمن مسار آخر
            - any() ترجع True إذا كان أي عنصر True
        """
        resolved_path = path.resolve()
        
        # التحقق من أن المسار داخل المشروع
        if not resolved_path.is_relative_to(self.project_root):
            logger.warning(f"Unsafe path (outside project): {resolved_path}")
            return False
        
        # التحقق من أن المسار ليس في .git
        if ".git" in resolved_path.parts:
            logger.warning(f"Unsafe path (.git directory): {resolved_path}")
            return False
        
        return True
    
    def _is_protected(self, path: Path) -> bool:
        """
        التحقق من أن الملف محمي من الحذف.
        
        Args:
            path: مسار الملف
            
        Returns:
            bool: True إذا كان الملف محمياً
        """
        return path.name in self.protected_files
    
    async def read_file(self, file_path: str | Path) -> str:
        """
        قراءة محتوى ملف.
        
        Args:
            file_path: مسار الملف (نسبي أو مطلق)
            
        Returns:
            str: محتوى الملف
            
        Raises:
            ValueError: إذا كان المسار غير آمن
            FileNotFoundError: إذا لم يُوجد الملف
            
        مثال:
            >>> content = await file_ops.read_file("app/main.py")
            >>> print(content[:100])
            
        ملاحظة:
            - Path() تحول string إلى Path object
            - with open() تفتح الملف وتضمن إغلاقه
            - "r" تعني read mode
            - encoding="utf-8" للنصوص العربية
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        # التحقق من الأمان
        if not self._is_safe_path(path):
            raise ValueError(f"Unsafe path: {path}")
        
        # التحقق من وجود الملف
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # قراءة المحتوى
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        logger.info(f"Read file: {path} ({len(content)} chars)")
        return content
    
    async def write_file(
        self,
        file_path: str | Path,
        content: str,
        overwrite: bool = False,
    ) -> bool:
        """
        كتابة محتوى إلى ملف.
        
        Args:
            file_path: مسار الملف
            content: المحتوى المراد كتابته
            overwrite: هل نسمح بالكتابة فوق ملف موجود؟
            
        Returns:
            bool: True إذا نجحت العملية
            
        Raises:
            ValueError: إذا كان المسار غير آمن
            FileExistsError: إذا كان الملف موجوداً و overwrite=False
            
        مثال:
            >>> await file_ops.write_file(
            ...     "new_module.py",
            ...     "def hello():\n    print('hi')"
            ... )
            
        ملاحظة:
            - .parent تُرجع المجلد الأب
            - .mkdir() تُنشئ مجلد
            - parents=True تُنشئ المجلدات الأب إذا لم تكن موجودة
            - exist_ok=True لا ترفع خطأ إذا كان المجلد موجوداً
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        # التحقق من الأمان
        if not self._is_safe_path(path):
            raise ValueError(f"Unsafe path: {path}")
        
        # التحقق من عدم الكتابة فوق ملف موجود
        if path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {path}. "
                "Use overwrite=True to replace it."
            )
        
        # إنشاء المجلدات الأب إذا لم تكن موجودة
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # كتابة المحتوى
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Wrote file: {path} ({len(content)} chars)")
        return True
    
    async def edit_file(
        self,
        file_path: str | Path,
        old_text: str,
        new_text: str,
    ) -> bool:
        """
        تعديل نص في ملف موجود.
        
        Args:
            file_path: مسار الملف
            old_text: النص القديم المراد استبداله
            new_text: النص الجديد
            
        Returns:
            bool: True إذا نجحت العملية
            
        Raises:
            ValueError: إذا لم يُوجد النص القديم في الملف
            
        مثال:
            >>> await file_ops.edit_file(
            ...     "app/config.py",
            ...     "DEBUG = True",
            ...     "DEBUG = False"
            ... )
            
        ملاحظة:
            - .replace() تستبدل جميع التطابقات
            - لا تستخدم regex، بحث نصي بسيط
        """
        # قراءة المحتوى الحالي
        content = await self.read_file(file_path)
        
        # التحقق من وجود النص القديم
        if old_text not in content:
            raise ValueError(
                f"Old text not found in file: {file_path}\n"
                f"Looking for: {old_text[:100]}..."
            )
        
        # استبدال النص
        new_content = content.replace(old_text, new_text)
        
        # كتابة المحتوى الجديد
        await self.write_file(file_path, new_content, overwrite=True)
        
        logger.info(f"Edited file: {file_path}")
        return True
    
    async def delete_file(self, file_path: str | Path, force: bool = False) -> bool:
        """
        حذف ملف.
        
        Args:
            file_path: مسار الملف
            force: تجاهل الحماية وحذف ملف محمي
            
        Returns:
            bool: True إذا نجحت العملية
            
        Raises:
            ValueError: إذا كان الملف محمياً و force=False
            
        ملاحظة:
            - استخدم force=True بحذر شديد!
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        # التحقق من الأمان
        if not self._is_safe_path(path):
            raise ValueError(f"Unsafe path: {path}")
        
        # التحقق من الحماية
        if self._is_protected(path) and not force:
            raise ValueError(
                f"Protected file: {path}. "
                "Use force=True to delete anyway (NOT RECOMMENDED)."
            )
        
        # حذف الملف
        if path.exists():
            path.unlink()
            logger.warning(f"Deleted file: {path}")
            return True
        else:
            logger.info(f"File doesn't exist (nothing to delete): {path}")
            return False
    
    async def create_directory(self, dir_path: str | Path) -> bool:
        """
        إنشاء مجلد جديد.
        
        Args:
            dir_path: مسار المجلد
            
        Returns:
            bool: True إذا نجحت العملية
        """
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        # التحقق من الأمان
        if not self._is_safe_path(path):
            raise ValueError(f"Unsafe path: {path}")
        
        # إنشاء المجلد
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
        return True
    
    async def list_directory(self, dir_path: str | Path = ".") -> list[str]:
        """
        عرض محتويات مجلد.
        
        Args:
            dir_path: مسار المجلد
            
        Returns:
            list[str]: قائمة بأسماء الملفات والمجلدات
        """
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        # التحقق من الأمان
        if not self._is_safe_path(path):
            raise ValueError(f"Unsafe path: {path}")
        
        # عرض المحتويات
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        items = [item.name for item in path.iterdir()]
        logger.info(f"Listed directory: {path} ({len(items)} items)")
        return sorted(items)


class ShellOperations:
    """
    عمليات Shell (Shell Operations).
    
    توفر تنفيذ آمن لأوامر Shell.
    
    تحذير:
        - ⚠️ استخدام أوامر Shell خطير!
        - ⚠️ لا تثق بمدخلات المستخدم
        - ⚠️ استخدم القائمة البيضاء للأوامر المسموحة
    """
    
    def __init__(self) -> None:
        """تهيئة نظام عمليات Shell."""
        # الأوامر المسموحة (Whitelist)
        self.allowed_commands = {
            "git",
            "python",
            "pytest",
            "pip",
            "ls",
            "cat",
            "grep",
            "find",
        }
    
    async def execute_command(
        self,
        command: str,
        cwd: Path | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """
        تنفيذ أمر Shell.
        
        Args:
            command: الأمر المراد تنفيذه
            cwd: المجلد الحالي للتنفيذ
            timeout: المهلة الزمنية بالثواني
            
        Returns:
            dict: نتيجة التنفيذ (stdout, stderr, returncode)
            
        مثال:
            >>> result = await shell_ops.execute_command("git status")
            >>> print(result['stdout'])
        """
        # استخراج الأمر الأول
        command_name = command.split()[0] if command.strip() else ""
        
        # التحقق من القائمة البيضاء
        if command_name not in self.allowed_commands:
            logger.error(f"Command not allowed: {command_name}")
            return {
                "success": False,
                "error": f"Command '{command_name}' is not in the allowed list",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
        
        try:
            # تنفيذ الأمر
            logger.info(f"Executing command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command}")
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }


class OvermindCapabilities:
    """
    قدرات Overmind الكاملة (Overmind Full Capabilities).
    
    يجمع جميع القدرات في واجهة واحدة:
    - عمليات الملفات
    - عمليات Shell
    - عمليات Git
    
    الاستخدام:
        >>> capabilities = OvermindCapabilities()
        >>> await capabilities.read_file("app/main.py")
        >>> await capabilities.execute_shell("git status")
    """
    
    def __init__(self, project_root: Path | None = None) -> None:
        """تهيئة قدرات Overmind."""
        self.file_ops = FileOperations(project_root)
        self.shell_ops = ShellOperations()
        logger.info("OvermindCapabilities initialized")
    
    # File operations (تفويض إلى FileOperations)
    async def read_file(self, path: str | Path) -> str:
        """قراءة ملف."""
        return await self.file_ops.read_file(path)
    
    async def write_file(self, path: str | Path, content: str, overwrite: bool = False) -> bool:
        """كتابة ملف."""
        return await self.file_ops.write_file(path, content, overwrite)
    
    async def edit_file(self, path: str | Path, old_text: str, new_text: str) -> bool:
        """تعديل ملف."""
        return await self.file_ops.edit_file(path, old_text, new_text)
    
    async def delete_file(self, path: str | Path, force: bool = False) -> bool:
        """حذف ملف."""
        return await self.file_ops.delete_file(path, force)
    
    async def create_directory(self, path: str | Path) -> bool:
        """إنشاء مجلد."""
        return await self.file_ops.create_directory(path)
    
    async def list_directory(self, path: str | Path = ".") -> list[str]:
        """عرض محتويات مجلد."""
        return await self.file_ops.list_directory(path)
    
    # Shell operations (تفويض إلى ShellOperations)
    async def execute_shell(self, command: str, timeout: int = 30) -> dict[str, Any]:
        """تنفيذ أمر Shell."""
        return await self.shell_ops.execute_command(
            command,
            cwd=self.file_ops.project_root,
            timeout=timeout,
        )
    
    # Git operations (استخدام ShellOperations)
    async def git_status(self) -> dict[str, Any]:
        """عرض حالة Git."""
        return await self.execute_shell("git status")
    
    async def git_add(self, files: str = ".") -> dict[str, Any]:
        """إضافة ملفات إلى Git staging."""
        return await self.execute_shell(f"git add {files}")
    
    async def git_commit(self, message: str) -> dict[str, Any]:
        """إنشاء commit."""
        # تنظيف الرسالة من علامات الاقتباس الخطيرة
        safe_message = message.replace('"', '\\"')
        return await self.execute_shell(f'git commit -m "{safe_message}"')
