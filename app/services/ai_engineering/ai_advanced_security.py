"""
🛡️ AI Advanced Security - LEGACY COMPATIBILITY SHIM
====================================================

**NOTICE**: This file is now a thin compatibility layer.

الأصل: 665 سطر من الكود الأحادي
Original: 665 lines of monolithic code

الجديد: معمارية سداسية منظمة في ai_security/
Refactored: Modular hexagonal architecture in ai_security/

التخفيض: ~91% (665 → ~60 سطر)
Reduction: ~91% (665 → ~60 lines)

For new code, import from: app.services.ai_security
للكود الجديد، استورد من: app.services.ai_security
"""

import warnings

# Import from refactored module
from app.services.ai_security import (
    # Domain Models
    SecurityEvent,
    # Facade
    SuperhumanSecuritySystem,
    ThreatDetection,
    ThreatLevel,
    ThreatType,
    UserBehaviorProfile,
    get_superhuman_security_system,
)

# Emit deprecation warning
warnings.warn(
    f"{__name__} is a legacy compatibility shim. "
    f"Please update imports to use app.services.ai_security instead. "
    f"This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything for backward compatibility
__all__ = [
    "AutomatedResponseSystem",
    "BehavioralAnalyzer",
    # Legacy aliases
    "DeepLearningThreatDetector",
    # Domain models
    "SecurityEvent",
    # Main service
    "SuperhumanSecuritySystem",
    "ThreatDetection",
    "ThreatLevel",
    "ThreatType",
    "UserBehaviorProfile",
    "get_superhuman_security_system",
]

# Legacy class aliases for backward compatibility
# These delegate to the new implementations
try:
    from app.services.ai_security.infrastructure import (
        DeepLearningThreatDetector,
    )
    from app.services.ai_security.infrastructure import (
        SimpleBehavioralAnalyzer as BehavioralAnalyzer,
    )
    from app.services.ai_security.infrastructure import (
        SimpleResponseSystem as AutomatedResponseSystem,
    )
except ImportError:
    # Fallback if infrastructure not fully imported
    DeepLearningThreatDetector = None
    BehavioralAnalyzer = None
    AutomatedResponseSystem = None
