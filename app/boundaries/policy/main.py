from __future__ import annotations

import logging

from .compliance import ComplianceEngine
from .engine import PolicyEngine
from .governance import DataGovernanceFramework
from .layers import (
    AuditLoggingLayer,
    AuthorizationLayer,
    InputValidationLayer,
    JWTValidationLayer,
    RateLimitingLayer,
    SecurityPipeline,
    TLSLayer,
)

logger = logging.getLogger(__name__)

class PolicyBoundary:
    """
    حدود السياسات (Policy Boundary)

    يجمع كل أنماط فصل السياسات في واجهة موحدة:
    - PolicyEngine للترخيص القائم على السياسات
    - SecurityPipeline للأمان متعدد الطبقات
    - ComplianceEngine لمتطلبات الامتثال
    - DataGovernanceFramework لحوكمة البيانات
    """

    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.security_pipeline = SecurityPipeline()
        self.compliance_engine = ComplianceEngine()
        self.data_governance = DataGovernanceFramework()

    def setup_default_security_layers(self) -> None:
        """إعداد طبقات الأمان الافتراضية"""
        self.security_pipeline.add_layer(TLSLayer())
        self.security_pipeline.add_layer(JWTValidationLayer())
        self.security_pipeline.add_layer(AuthorizationLayer(self.policy_engine))
        self.security_pipeline.add_layer(InputValidationLayer())
        self.security_pipeline.add_layer(RateLimitingLayer())
        self.security_pipeline.add_layer(AuditLoggingLayer())
        logger.info("✅ Default security layers configured")


# ======================================================================================
# GLOBAL INSTANCE (اختياري)
# ======================================================================================

_global_policy_boundary: PolicyBoundary | None = None


def get_policy_boundary() -> PolicyBoundary:
    """الحصول على مثيل عام من حدود السياسات"""
    global _global_policy_boundary
    if _global_policy_boundary is None:
        _global_policy_boundary = PolicyBoundary()
        _global_policy_boundary.setup_default_security_layers()
    return _global_policy_boundary
