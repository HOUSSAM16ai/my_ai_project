# app/core/static_handler.py
"""
Static File Serving & SPA Fallback Handler.
Encapsulates logic for serving the frontend and handling routing for Single Page Applications.
"""

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


def setup_static_files(app: FastAPI, static_dir: str | None = None) -> None:
    """
    Sets up static file serving and SPA fallback.
    User requirement: Serve app/static directly. No dist/. No build.
    """
    static_files_dir = static_dir or os.path.join(os.getcwd(), "app/static")

    if not os.path.exists(static_files_dir):
        logger.warning(
            f"Static files directory not found: {static_files_dir}. Frontend will not be served."
        )
        return

    # 1. Mount specific assets folders (css, js, src) so they are accessible directly
    for folder in ["css", "js", "src"]:
        folder_path = os.path.join(static_files_dir, folder)
        if os.path.isdir(folder_path):
            app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)

    # 2. Serve index.html at root
    async def serve_root():
        return FileResponse(os.path.join(static_files_dir, "index.html"))

    app.add_api_route("/", serve_root, methods=["GET", "HEAD"])

    # 3. SPA Fallback: serve index.html for non-API routes
    async def spa_fallback(request: Request, full_path: str):
        # 1. First, check if the file physically exists in static directory
        # This ensures that if we have /documentation/api/guide.html, it gets served
        # even if it contains "api" in the path.
        potential_path = os.path.normpath(os.path.join(static_files_dir, full_path))

        # Safety check for directory traversal
        if not potential_path.startswith(static_files_dir):
            # traversal attempt
            raise HTTPException(status_code=404, detail="Not Found")

        # If a specific file exists in static (e.g. /superhuman_dashboard.html), serve it
        if os.path.isfile(potential_path):
            # Ensure we only serve GET/HEAD for static files unless configured otherwise
            if request.method not in ["GET", "HEAD"]:
                raise HTTPException(status_code=405, detail="Method Not Allowed")
            return FileResponse(potential_path)

        # 2. If file doesn't exist, THEN enforce API restrictions
        # If path starts with api or contains /api/, return 404 (don't serve HTML)
        # This ensures nested API routes (e.g. /admin/api/...) also return 404 when not found
        if full_path.startswith("api") or "/api/" in full_path or full_path.endswith("/api"):
            raise HTTPException(status_code=404, detail="Not Found")

        # 3. If it is NOT a GET/HEAD request, and it fell through to here, it's a 404
        if request.method not in ["GET", "HEAD"]:
            raise HTTPException(status_code=404, detail="Not Found")

        # 4. Otherwise serve index.html (SPA)
        return FileResponse(os.path.join(static_files_dir, "index.html"))

    # Register the catch-all route for SPA history mode
    app.add_api_route(
        "/{full_path:path}",
        spa_fallback,
        methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )
