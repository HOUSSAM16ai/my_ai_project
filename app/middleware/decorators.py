# app/middleware/decorators.py
# ======================================================================================
# ==               UNIFIED DECORATOR EXPORTS - SUPERHUMAN MIDDLEWARE                 ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نقطة مركزية موحدة لتصدير جميع الديكوراتورات من الخدمات المختلفة
#   Unified central point for exporting all decorators from various services
#
# Purpose:
#   This module provides a single import location for all API decorators,
#   regardless of where they're actually implemented. This follows the
#   Single Responsibility Principle and makes imports cleaner.
#
# Design Philosophy:
#   - Decorators are implemented in their respective service modules
#   - This module acts as a facade, re-exporting them for convenience
#   - Changes to service modules don't affect import statements
#   - Provides better developer experience with autocomplete
#
# Usage:
#   from app.middleware.decorators import rate_limit, monitor_performance, require_jwt_auth
#
# Benefits:
#   ✅ Centralized import location
#   ✅ Clean separation of concerns
#   ✅ Backward compatibility
#   ✅ Easy to maintain
#   ✅ Future-proof architecture
# ======================================================================================

# Security decorators from api_security_service
from app.services.api_security_service import (
    require_jwt_auth,
    rate_limit,
)

# Observability decorators from api_observability_service
from app.services.api_observability_service import (
    monitor_performance,
)

# Export all decorators for clean imports
__all__ = [
    'require_jwt_auth',
    'rate_limit',
    'monitor_performance',
]
