"""
Utility modules for common functionality.
This package contains reusable utility functions to reduce code duplication.
"""
from .model_registry import ModelRegistry, get_admin_conversation_model, get_admin_message_model, get_mission_model, get_task_model, get_user_model
from .service_locator import ServiceLocator, get_admin_ai, get_database_service, get_maestro, get_overmind
from .text_processing import extract_first_json_object, strip_markdown_fences

__all__ = [
    # Text processing
    "strip_markdown_fences",
    "extract_first_json_object",
    # Model registry
    "ModelRegistry",
    "get_mission_model",
    "get_task_model",
    "get_user_model",
    "get_admin_conversation_model",
    "get_admin_message_model",
    # Service locator
    "ServiceLocator",
    "get_overmind",
    "get_maestro",
    "get_admin_ai",
    "get_database_service",
]

