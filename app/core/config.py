import warnings

from app.core.settings.base import AppSettings, BaseServiceSettings, get_settings

# Deprecation Warning for using this module directly
warnings.warn(
    "Importing from 'app.core.config' is deprecated. "
    "Use 'app.core.settings.base' for settings and 'app.core.settings' for specific service configs.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["AppSettings", "BaseServiceSettings", "get_settings"]
