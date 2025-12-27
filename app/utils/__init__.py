"""
Utility modules for common functionality.
This package contains reusable utility functions to reduce code duplication.
"""

from .model_registry import (
    ModelRegistry,
    get_admin_conversation_model,
    get_admin_message_model,
    get_mission_model,
    get_task_model,
    get_user_model,
)
from .service_locator import (
    ServiceLocator,
    get_database_service,
)
from .text_processing import extract_first_json_object, strip_markdown_fences

__all__ = [
    # Model registry
    "ModelRegistry",
    # Service locator
    "ServiceLocator",
    "extract_first_json_object",
    "get_admin_conversation_model",
    "get_admin_message_model",
    "get_database_service",
    "get_mission_model",
    "get_task_model",
    "get_user_model",
    # Text processing
    "strip_markdown_fences",
]
