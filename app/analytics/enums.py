"""Analytics domain enumerations."""

from enum import Enum


class EventType(Enum):
    """User event types"""

    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    CONVERSION = "conversion"
    PURCHASE = "purchase"
    SIGNUP = "signup"
    LOGIN = "login"
    LOGOUT = "logout"
    FEATURE_USE = "feature_use"
    ERROR = "error"
    CUSTOM = "custom"


class UserSegment(Enum):
    """User segment types"""

    NEW = "new"
    ACTIVE = "active"
    POWER = "power"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    RESURRECTED = "resurrected"


class ABTestVariant(Enum):
    """A/B test variant types"""

    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"
