# app/middleware/cors/__init__.py
# ======================================================================================
# ==                    MIDDLEWARE CORS MODULE (v∞ - Aurora Edition)                ==
# ======================================================================================
"""
وحدة CORS - CORS Module

Cross-Origin Resource Sharing configuration and middleware.
"""

from .cors_middleware import CORSMiddleware

__all__ = ["CORSMiddleware"]
__version__ = "1.0.0-aurora"
