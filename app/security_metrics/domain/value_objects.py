"""Value objects for security metrics domain."""

from enum import Enum

class Severity(Enum):
    """Security finding severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class RiskLevel(Enum):
    """Risk assessment levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MINIMAL = "MINIMAL"

class TrendDirection(Enum):
    """Security trend directions."""

    IMPROVING = "IMPROVING"
    DEGRADING = "DEGRADING"
    STABLE = "STABLE"
