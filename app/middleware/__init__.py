# ======================================================================================
# ==                    API MIDDLEWARE MODULE (v1.0)                                 ==
# ======================================================================================

from app.middleware.cors_config import setup_cors
from app.middleware.error_handler import setup_error_handlers
from app.middleware.request_logger import setup_request_logging

__all__ = ["setup_error_handlers", "setup_cors", "setup_request_logging"]
