"""
Model Registry - Centralized Model Access
==========================================

This module provides a centralized registry for database models to reduce
coupling between modules. Instead of importing models directly from app.models
in many files, components can use this registry.

Benefits:
- Reduces import coupling
- Single point for model access
- Easier to track model usage
- Facilitates lazy loading
"""
from typing import Type, TypeVar

# Type variable for generic model types
T = TypeVar("T")


class ModelRegistry:
    """
    Centralized registry for database models.
    
    This class provides lazy-loaded access to models, reducing circular
    import issues and coupling between modules.
    """
    
    _models_cache = {}
    
    @classmethod
    def get_model(cls, model_name: str) -> Type:
        """
        Get a model class by name.
        
        Args:
            model_name: Name of the model (e.g., 'Mission', 'Task', 'User')
            
        Returns:
            Model class
            
        Raises:
            ValueError: If model not found
        """
        if model_name in cls._models_cache:
            return cls._models_cache[model_name]
        
        # Lazy import to avoid circular dependencies
        try:
            from app import models
            model_class = getattr(models, model_name, None)
            
            if model_class is None:
                raise ValueError(f"Model '{model_name}' not found in app.models")
            
            cls._models_cache[model_name] = model_class
            return model_class
            
        except ImportError as e:
            raise ValueError(f"Cannot import models module: {e}")
    
    @classmethod
    def clear_cache(cls):
        """Clear the model cache. Useful for testing."""
        cls._models_cache.clear()


# Convenience functions for commonly used models
def get_mission_model():
    """Get the Mission model class."""
    return ModelRegistry.get_model("Mission")


def get_task_model():
    """Get the Task model class."""
    return ModelRegistry.get_model("Task")


def get_user_model():
    """Get the User model class."""
    return ModelRegistry.get_model("User")


def get_admin_conversation_model():
    """Get the AdminConversation model class."""
    return ModelRegistry.get_model("AdminConversation")


def get_admin_message_model():
    """Get the AdminMessage model class."""
    return ModelRegistry.get_model("AdminMessage")
