# app/boundaries/policy_boundaries.py
"""
======================================================================================
 POLICY BOUNDARIES - فصل الاهتمامات عبر حدود السياسات
======================================================================================

DEPRECATION NOTICE:
  This file is now a facade for the modular package `app.boundaries.policy`.
  Please import from the new package directly.
  تم إعادة هيكلة هذا الملف إلى حزمة `app.boundaries.policy`.

PURPOSE (الغرض):
  فصل سياسات الأمان والامتثال عن منطق التطبيق

PATTERNS IMPLEMENTED (الأنماط المطبقة):
  1. Policy-Based Authorization (الترخيص القائم على السياسات)
  2. Multi-Layer Security (الأمان متعدد الطبقات)
  3. Policy as Code (السياسات كشفرة برمجية)
  4. Compliance Engine (محرك الامتثال)
  5. Data Governance Framework (إطار حوكمة البيانات)

KEY PRINCIPLES (المبادئ الأساسية):
  - فصل المصادقة عن الترخيص
  - كل طبقة أمان مستقلة وقابلة للاختبار
  - السياسات قابلة للقراءة والإدارة
  - الامتثال منفصل عن منطق العمل
  - حوكمة البيانات موحدة

IMPLEMENTATION DATE: 2025-11-05
REFACTORED DATE: 2025-02-24
VERSION: 1.1.0
======================================================================================
"""

from app.boundaries.policy import (
    Principal,
    AuthenticationService,
    PolicyEngine,
    Policy,
    PolicyRule,
    Effect,
    SecurityLayer,
    SecurityPipeline,
    SecurityException,
    TLSLayer,
    JWTValidationLayer,
    AuthorizationLayer,
    InputValidationLayer,
    RateLimitingLayer,
    AuditLoggingLayer,
    ComplianceEngine,
    ComplianceRule,
    ComplianceRegulation,
    DataGovernanceFramework,
    DataGovernancePolicy,
    DataClassification,
    PolicyBoundary,
    get_policy_boundary
)

__all__ = [
    "Principal",
    "AuthenticationService",
    "PolicyEngine",
    "Policy",
    "PolicyRule",
    "Effect",
    "SecurityLayer",
    "SecurityPipeline",
    "SecurityException",
    "TLSLayer",
    "JWTValidationLayer",
    "AuthorizationLayer",
    "InputValidationLayer",
    "RateLimitingLayer",
    "AuditLoggingLayer",
    "ComplianceEngine",
    "ComplianceRule",
    "ComplianceRegulation",
    "DataGovernanceFramework",
    "DataGovernancePolicy",
    "DataClassification",
    "PolicyBoundary",
    "get_policy_boundary",
]
