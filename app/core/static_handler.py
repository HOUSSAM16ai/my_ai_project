"""
معالج الملفات الثابتة (Static File Handler).

يتولى مسؤولية تقديم ملفات الواجهة الأمامية (Frontend) والتعامل مع توجيه SPA (Single Page Application).
يطبق مبادئ CS50 (التوثيق) و SICP (فصل الاهتمامات).

المعايير (Standards):
- Strict Types: استخدام الأنواع الصارمة.
- Arabic Docs: توثيق عربي كامل.
- Security: منع تجاوز المسار (Path Traversal).
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

# TODO: Split this function (78 lines) - KISS principle
def setup_static_files(app: FastAPI, static_dir: str | None = None) -> None:
    """
    إعداد خدمة الملفات الثابتة واستراتيجية الرد (Fallback) لتطبيقات الصفحة الواحدة.

    هذه الدالة تقوم بـ:
    1. ربط المجلدات الفرعية (css, js) مباشرة لسرعة الوصول.
    2. إعداد نقطة الجذر (Root) لخدمة index.html.
    3. إعداد معالج SPA Fallback لخدمة index.html للمسارات غير الموجودة (ما عدا API).

    Args:
        app: تطبيق FastAPI.
        static_dir: مسار مجلد الملفات الثابتة (اختياري).
    """
    # تحديد مسار الملفات الثابتة (الافتراضي: app/static)
    base_static_dir = static_dir or os.path.join(os.getcwd(), "app/static")

    if not os.path.exists(base_static_dir):
        logger.warning(
            f"⚠️ Static files directory not found: {base_static_dir}. Frontend will not be served."
        )
        return

    logger.info(f"📂 Mounting static files from: {base_static_dir}")

    # 1. ربط المجلدات المحددة (Mount Specific Folders)
    for folder in MOUNTABLE_FOLDERS:
        folder_path = os.path.join(base_static_dir, folder)
        if os.path.isdir(folder_path):
            app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)

    # 2. خدمة الصفحة الرئيسية (Serve Index)
    async def serve_root() -> FileResponse:
        """يخدم ملف index.html عند طلب الجذر."""
        return FileResponse(os.path.join(base_static_dir, "index.html"))

    app.add_api_route("/", serve_root, methods=["GET", "HEAD"])

    # 3. معالج SPA Fallback (SPA Catch-all)
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        """
        يتعامل مع المسارات غير الموجودة.

        الخوارزمية:
        1. التحقق من وجود ملف فعلي آمن (Physical File Check).
        2. رفض طلبات API غير الموجودة (404).
        3. رفض الطرق غير الآمنة (Non-GET).
        4. خدمة index.html كحل أخير (SPA Routing).
        """
        # 1. تطبيع المسار وفحص الأمان
        potential_path = os.path.normpath(os.path.join(base_static_dir, full_path))

        # Security: منع Path Traversal
        if not potential_path.startswith(base_static_dir):
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
        return FileResponse(os.path.join(base_static_dir, "index.html"))

    # تسجيل المسار العام
    app.add_api_route(
        "/{full_path:path}",
        spa_fallback,
        methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )
