"""
Static Files Middleware - منفصل تماماً عن API Core.

هذا الملف يمثل middleware اختياري لخدمة الملفات الثابتة (Frontend).
المبدأ: API-First Architecture - يمكن تشغيل API بدون frontend.

المعايير (Standards):
- Strict Types: استخدام الأنواع الصارمة.
- Arabic Docs: توثيق عربي كامل.
- Security: منع تجاوز المسار (Path Traversal).
- Optional: يمكن تعطيل هذا Middleware بالكامل.
"""

import logging
import os
from typing import Final

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

# المجلدات المسموح بتقديمها مباشرة
MOUNTABLE_FOLDERS: Final[list[str]] = ["css", "js", "src", "assets"]


class StaticFilesConfig:
    """
    إعدادات خدمة الملفات الثابتة.
    
    يسمح بتكوين كامل لكيفية خدمة الملفات الثابتة بشكل منفصل عن API.
    """
    
    def __init__(
        self,
        *,
        enabled: bool = True,
        static_dir: str | None = None,
        mount_folders: list[str] | None = None,
        serve_spa: bool = True,
    ) -> None:
        """
        تهيئة إعدادات الملفات الثابتة.
        
        Args:
            enabled: تفعيل/تعطيل خدمة الملفات الثابتة.
            static_dir: مسار مجلد الملفات الثابتة.
            mount_folders: قائمة المجلدات المسموح بتقديمها.
            serve_spa: تفعيل SPA fallback routing.
        """
        self.enabled = enabled
        self.static_dir = static_dir or os.path.join(os.getcwd(), "app/static")
        self.mount_folders = mount_folders or MOUNTABLE_FOLDERS
        self.serve_spa = serve_spa


def setup_static_files_middleware(
    app: FastAPI,
    config: StaticFilesConfig | None = None,
) -> None:
    """
    إعداد خدمة الملفات الثابتة كـ middleware اختياري منفصل.
    
    هذه الدالة مستقلة تماماً عن API core وتستدعى فقط عند الحاجة.
    
    المبدأ: Separation of Concerns - API Core لا يعرف شيئاً عن Frontend.
    
    Args:
        app: تطبيق FastAPI.
        config: إعدادات الملفات الثابتة (اختياري).
    """
    # استخدام الإعدادات الافتراضية إذا لم يتم توفيرها
    if config is None:
        config = StaticFilesConfig()
    
    # التحقق من التفعيل
    if not config.enabled:
        logger.info("🚫 Static files serving is DISABLED (API-only mode)")
        return
    
    # التحقق من وجود المجلد
    if not os.path.exists(config.static_dir):
        logger.warning(
            f"⚠️ Static files directory not found: {config.static_dir}. "
            "Running in API-only mode."
        )
        return
    
    logger.info(f"📂 Mounting static files from: {config.static_dir}")
    
    # 1. ربط المجلدات المحددة (Mount Specific Folders)
    for folder in config.mount_folders:
        folder_path = os.path.join(config.static_dir, folder)
        if os.path.isdir(folder_path):
            app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)
            logger.debug(f"   ✓ Mounted /{folder}")
    
    # 2. خدمة الصفحة الرئيسية (Serve Index)
    async def serve_root() -> FileResponse:
        """يخدم ملف index.html عند طلب الجذر."""
        return FileResponse(os.path.join(config.static_dir, "index.html"))
    
    app.add_api_route("/", serve_root, methods=["GET", "HEAD"], include_in_schema=False)
    
    # 3. معالج SPA Fallback (إذا كان مفعلاً)
    if config.serve_spa:
        async def spa_fallback(request: Request, full_path: str) -> FileResponse:
            """
            يتعامل مع المسارات غير الموجودة (SPA Routing).
            
            الخوارزمية:
            1. التحقق من وجود ملف فعلي آمن.
            2. رفض طلبات API غير الموجودة (404).
            3. رفض الطرق غير الآمنة (Non-GET).
            4. خدمة index.html كحل أخير (SPA Routing).
            """
            # 1. تطبيع المسار وفحص الأمان
            potential_path = os.path.normpath(os.path.join(config.static_dir, full_path))
            
            # Security: منع Path Traversal
            if not potential_path.startswith(config.static_dir):
                raise HTTPException(status_code=404, detail="Not Found")
            
            # إذا كان الملف موجوداً، نخدمه
            if os.path.isfile(potential_path):
                if request.method not in ["GET", "HEAD"]:
                    raise HTTPException(status_code=405, detail="Method Not Allowed")
                return FileResponse(potential_path)
            
            # 2. حماية مسارات API
            # أي طلب يبدأ بـ api أو يحتوي عليه لا يجب أن يعيد HTML
            if full_path.startswith("api") or "/api/" in full_path or full_path.endswith("/api"):
                raise HTTPException(status_code=404, detail="Not Found")
            
            # 3. التحقق من الطريقة
            if request.method not in ["GET", "HEAD"]:
                raise HTTPException(status_code=404, detail="Not Found")
            
            # 4. التوجيه إلى SPA
            return FileResponse(os.path.join(config.static_dir, "index.html"))
        
        # تسجيل المسار العام (أقل أولوية من API routes)
        app.add_api_route(
            "/{full_path:path}",
            spa_fallback,
            methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            include_in_schema=False,
        )
    
    logger.info("✅ Static files middleware configured successfully")
