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
    
    Setup static files serving as optional, decoupled middleware.
    
    هذه الدالة مستقلة تماماً عن API core وتستدعى فقط عند الحاجة.
    This function is completely independent of API core and called only when needed.
    
    المبدأ: Separation of Concerns - API Core لا يعرف شيئاً عن Frontend.
    Principle: Separation of Concerns - API Core knows nothing about Frontend.
    
    Args:
        app: FastAPI application تطبيق
        config: Static files configuration (optional) إعدادات الملفات الثابتة
    """
    # Use default config if not provided
    if config is None:
        config = StaticFilesConfig()
    
    # Check if enabled
    if not _should_enable_static_files(config):
        return
    
    logger.info(f"📂 Mounting static files from: {config.static_dir}")
    
    # Setup static files serving
    _mount_static_folders(app, config)
    _setup_root_route(app, config)
    
    if config.serve_spa:
        _setup_spa_fallback(app, config)
    
    logger.info("✅ Static files middleware configured successfully")


def _should_enable_static_files(config: StaticFilesConfig) -> bool:
    """
    Check if static files serving should be enabled.
    
    التحقق مما إذا كان يجب تفعيل خدمة الملفات الثابتة.
    """
    if not config.enabled:
        logger.info("🚫 Static files serving is DISABLED (API-only mode)")
        return False
    
    if not os.path.exists(config.static_dir):
        logger.warning(
            f"⚠️ Static files directory not found: {config.static_dir}. "
            "Running in API-only mode."
        )
        return False
    
    return True


def _mount_static_folders(app: FastAPI, config: StaticFilesConfig) -> None:
    """
    Mount specific static folders to the app.
    
    ربط المجلدات الثابتة المحددة بالتطبيق.
    """
    for folder in config.mount_folders:
        folder_path = os.path.join(config.static_dir, folder)
        if os.path.isdir(folder_path):
            app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)
            logger.debug(f"   ✓ Mounted /{folder}")


def _setup_root_route(app: FastAPI, config: StaticFilesConfig) -> None:
    """
    Setup root route to serve index.html.
    
    إعداد مسار الجذر لخدمة index.html.
    """
    async def serve_root() -> FileResponse:
        """Serve index.html at root يخدم ملف index.html عند طلب الجذر"""
        return FileResponse(os.path.join(config.static_dir, "index.html"))
    
    app.add_api_route("/", serve_root, methods=["GET", "HEAD"], include_in_schema=False)


def _setup_spa_fallback(app: FastAPI, config: StaticFilesConfig) -> None:
    """
    Setup SPA fallback routing for client-side routing.
    
    إعداد التوجيه الاحتياطي لـ SPA للتوجيه من جانب العميل.
    """
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        """
        Handle missing routes for SPA routing.
        
        يتعامل مع المسارات غير الموجودة (SPA Routing).
        
        Algorithm الخوارزمية:
        1. Check for actual safe file التحقق من وجود ملف فعلي آمن
        2. Reject missing API requests رفض طلبات API غير الموجودة
        3. Reject unsafe methods رفض الطرق غير الآمنة
        4. Serve index.html as fallback خدمة index.html كحل أخير
        """
        # Try to serve actual file if it exists
        potential_path = os.path.normpath(os.path.join(config.static_dir, full_path))
        
        # Security: Prevent path traversal منع تجاوز المسار
        if not potential_path.startswith(config.static_dir):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Serve file if exists
        if os.path.isfile(potential_path):
            if request.method not in ["GET", "HEAD"]:
                raise HTTPException(status_code=405, detail="Method Not Allowed")
            return FileResponse(potential_path)
        
        # Protect API routes - حماية مسارات API
        if _is_api_path(full_path):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Only allow safe methods for SPA fallback
        if request.method not in ["GET", "HEAD"]:
            raise HTTPException(status_code=404, detail="Not Found")
        
        # SPA fallback - serve index.html
        return FileResponse(os.path.join(config.static_dir, "index.html"))
    
    # Register catch-all route (lowest priority after API routes)
    app.add_api_route(
        "/{full_path:path}",
        spa_fallback,
        methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        include_in_schema=False,
    )


def _is_api_path(path: str) -> bool:
    """
    Check if path is an API route.
    
    التحقق مما إذا كان المسار هو مسار API.
    """
    return path.startswith("api") or "/api/" in path or path.endswith("/api")
