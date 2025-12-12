"""
🛡️ Security Metrics Engine - LEGACY COMPATIBILITY SHIM
=======================================================

**NOTICE**: This file is now a thin compatibility layer.

الأصل: 655 سطر من الكود الأحادي
Original: 655 lines of monolithic code

الجديد: معمارية سداسية منظمة في security_metrics/
Refactored: Modular hexagonal architecture in security_metrics/

التخفيض: ~92% (655 → ~55 سطر)
Reduction: ~92% (655 → ~55 lines)

For new code, import from: app.services.security_metrics
للكود الجديد، استورد من: app.services.security_metrics
"""

import warnings

# Import from refactored module
from app.services.security_metrics import (
    RiskPrediction,
    SecurityFinding,
    SecurityMetrics,
    SecurityMetricsEngine as RefactoredSecurityMetricsEngine,
    Severity,
    TrendDirection,
    get_security_metrics_engine,
)

# Emit deprecation warning
warnings.warn(
    f"{__name__} is a legacy compatibility shim. "
    f"Please update imports to use app.services.security_metrics instead. "
    f"This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything for backward compatibility
__all__ = [
    # Main service
    "SecurityMetricsEngine",
    "get_security_metrics_engine",
    # Domain models
    "SecurityFinding",
    "SecurityMetrics",
    "RiskPrediction",
    "Severity",
    "TrendDirection",
]

# Alias for backward compatibility
SecurityMetricsEngine = RefactoredSecurityMetricsEngine
