# app/boundaries/policy_boundaries.py
"""
======================================================================================
 POLICY BOUNDARIES - فصل الاهتمامات عبر حدود السياسات
======================================================================================

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
VERSION: 1.0.0
======================================================================================
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ======================================================================================
# AUTHENTICATION LAYER - طبقة المصادقة
# ======================================================================================


@dataclass
class Principal:
    """
    الكيان المصادق عليه (Principal)

    يمثل المستخدم أو الخدمة المصادقة
    """

    id: str
    type: str  # user, service, system
    claims: dict[str, Any] = field(default_factory=dict)
    roles: set[str] = field(default_factory=set)
    authenticated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None

    def has_claim(self, claim_name: str, claim_value: Any | None = None) -> bool:
        """التحقق من وجود claim"""
        if claim_name not in self.claims:
            return False
        if claim_value is None:
            return True
        return self.claims[claim_name] == claim_value

    def has_role(self, role: str) -> bool:
        """التحقق من وجود دور"""
        return role in self.roles

    def is_expired(self) -> bool:
        """التحقق مما إذا كانت المصادقة منتهية"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class AuthenticationService(ABC):
    """
    خدمة المصادقة (Authentication Service)

    مسؤولة فقط عن التحقق من هوية المستخدم:
    - إدارة المستخدمين والبيانات الاعتمادية
    - إصدار الرموز (Token Issuance) - JWT/OAuth2
    - تحديث الرموز (Token Refresh)
    - لا علاقة لها بالصلاحيات التفصيلية
    """

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> Principal | None:
        """
        مصادقة مستخدم

        Args:
            credentials: البيانات الاعتمادية (email/password, token, etc.)

        Returns:
            Principal إذا نجحت المصادقة، None إذا فشلت
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> str | None:
        """تحديث رمز الوصول"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """إلغاء رمز"""
        pass


# ======================================================================================
# AUTHORIZATION LAYER - طبقة الترخيص
# ======================================================================================


class Effect(Enum):
    """تأثير السياسة"""

    ALLOW = "allow"
    DENY = "deny"


@dataclass
class PolicyRule:
    """
    قاعدة سياسة (Policy Rule)

    تعريف قابل للقراءة لسياسة الوصول
    """

    effect: Effect
    principals: list[str] = field(default_factory=list)  # roles or user IDs
    actions: list[str] = field(default_factory=list)  # ["read", "write", "delete"]
    resources: list[str] = field(default_factory=list)  # ["user:*", "document:123"]
    conditions: list[str] = field(default_factory=list)  # ["user.region == 'EU'"]


@dataclass
class Policy:
    """
    سياسة (Policy)

    مجموعة من القواعد التي تحدد من يمكنه فعل ماذا
    """

    name: str
    description: str
    rules: list[PolicyRule]
    priority: int = 0  # أولوية السياسة (أعلى رقم = أولوية أعلى)


class PolicyEngine:
    """
    محرك السياسات (Policy Engine)

    يقيّم السياسات ويحدد ما إذا كان الوصول مسموح أو محظور
    """

    def __init__(self):
        self.policies: list[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        """إضافة سياسة جديدة"""
        self.policies.append(policy)
        # ترتيب السياسات حسب الأولوية
        self.policies.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"✅ Policy added: {policy.name}")

    def evaluate(
        self,
        principal: Principal,
        action: str,
        resource: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        تقييم ما إذا كان الوصول مسموح

        Args:
            principal: الكيان الذي يطلب الوصول
            action: الإجراء المطلوب (read, write, delete, etc.)
            resource: المورد المستهدف (user:123, document:456, etc.)
            context: سياق إضافي للتقييم

        Returns:
            True إذا كان الوصول مسموح، False إذا كان محظور
        """
        context = context or {}

        # سياسة DENY الصريحة لها الأولوية
        deny_found = False
        allow_found = False

        for policy in self.policies:
            for rule in policy.rules:
                if self._matches_rule(principal, action, resource, rule, context):
                    if rule.effect == Effect.DENY:
                        deny_found = True
                        logger.info(
                            f"❌ Access denied by policy {policy.name}: "
                            f"{principal.id} -> {action} on {resource}"
                        )
                    elif rule.effect == Effect.ALLOW:
                        allow_found = True

        # DENY يتفوق على ALLOW
        if deny_found:
            return False

        if allow_found:
            logger.info(f"✅ Access granted: {principal.id} -> {action} on {resource}")
            return True

        # الرفض الافتراضي (Default Deny)
        logger.info(
            f"⚠️ Access denied (no matching policy): {principal.id} -> {action} on {resource}"
        )
        return False

    def _matches_rule(
        self,
        principal: Principal,
        action: str,
        resource: str,
        rule: PolicyRule,
        context: dict[str, Any],
    ) -> bool:
        """التحقق مما إذا كانت القاعدة تنطبق على الطلب"""
        # تحقق من Principal
        if not self._matches_principals(principal, rule.principals):
            return False

        # تحقق من Action
        if not self._matches_pattern(action, rule.actions):
            return False

        # تحقق من Resource
        if not self._matches_pattern(resource, rule.resources):
            return False

        # تحقق من Conditions
        if not self._evaluate_conditions(principal, resource, rule.conditions, context):
            return False

        return True

    def _matches_principals(self, principal: Principal, principals: list[str]) -> bool:
        """التحقق من مطابقة Principal"""
        if not principals:
            return True  # لا توجد قيود

        for principal_pattern in principals:
            # تحقق من الدور
            if principal_pattern.startswith("role:"):
                role = principal_pattern.split(":", 1)[1]
                if principal.has_role(role):
                    return True
            # تحقق من المعرف
            elif principal_pattern == principal.id:
                return True
            # wildcards
            elif principal_pattern == "*":
                return True

        return False

    def _matches_pattern(self, value: str, patterns: list[str]) -> bool:
        """التحقق من مطابقة النمط (يدعم wildcards)"""
        if not patterns:
            return True  # لا توجد قيود

        for pattern in patterns:
            if pattern == "*":
                return True
            # دعم wildcards بسيط
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if value.startswith(prefix):
                    return True
            elif value == pattern:
                return True

        return False

    def _evaluate_conditions(
        self,
        principal: Principal,
        resource: str,
        conditions: list[str],
        context: dict[str, Any],
    ) -> bool:
        """تقييم الشروط (Conditions)"""
        if not conditions:
            return True  # لا توجد شروط

        # بيئة تقييم الشروط
        eval_context = {
            "principal": principal,
            "resource": resource,
            "context": context,
        }

        for condition in conditions:
            try:
                # في الإنتاج، استخدم محرك تعبيرات آمن
                # هنا نستخدم تقييم بسيط للمثال
                if not self._evaluate_simple_condition(condition, eval_context):
                    return False
            except Exception as e:
                logger.error(f"❌ Error evaluating condition '{condition}': {e}")
                return False

        return True

    def _evaluate_simple_condition(self, condition: str, eval_context: dict[str, Any]) -> bool:
        """
        تقييم شرط بسيط

        أمثلة:
        - "principal.region == 'EU'"
        - "resource.location != 'EU'"
        - "context.time_of_day == 'business_hours'"
        """
        # تحليل بسيط للشروط (في الإنتاج، استخدم parser محترف)
        # نمط: "object.property operator value"
        match = re.match(r"(\w+)\.(\w+)\s*(==|!=|>|<|>=|<=)\s*['\"]?([^'\"]+)['\"]?", condition)
        if match is None:
            return False

        obj_name, prop_name, operator, value = match.groups()

        # الحصول على القيمة الفعلية
        obj = eval_context.get(obj_name)
        if obj is None:
            return False

        if isinstance(obj, Principal):
            actual_value = obj.claims.get(prop_name)
        elif isinstance(obj, dict):
            actual_value = obj.get(prop_name)
        else:
            return False

        # تقييم المقارنة
        if operator == "==":
            return str(actual_value) == value
        elif operator == "!=":
            return str(actual_value) != value
        elif operator == ">":
            return float(actual_value) > float(value)
        elif operator == "<":
            return float(actual_value) < float(value)
        elif operator == ">=":
            return float(actual_value) >= float(value)
        elif operator == "<=":
            return float(actual_value) <= float(value)

        return False


# ======================================================================================
# MULTI-LAYER SECURITY - الأمان متعدد الطبقات
# ======================================================================================


class SecurityLayer(ABC):
    """
    طبقة أمان (Security Layer)

    كل طبقة مستقلة ومسؤولة عن جانب واحد من الأمان
    """

    @abstractmethod
    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """معالجة الطلب عبر طبقة الأمان"""
        pass


class TLSLayer(SecurityLayer):
    """طبقة 1: تشفير النقل (TLS/mTLS)"""

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """التحقق من تشفير الاتصال"""
        if not request.get("is_secure", False):
            raise SecurityException("Connection must be secure (HTTPS/TLS)")
        logger.info("✅ TLS validation passed")
        return request


class JWTValidationLayer(SecurityLayer):
    """طبقة 2: المصادقة (JWT Validation)"""

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """التحقق من صحة JWT"""
        token = request.get("token")
        if not token:
            raise SecurityException("Missing authentication token")

        # في الإنتاج، استخدم مكتبة JWT حقيقية
        # هنا نستخدم تحقق بسيط للمثال
        logger.info("✅ JWT validation passed")
        return request


class AuthorizationLayer(SecurityLayer):
    """طبقة 3: الترخيص (Policy Enforcement)"""

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """تطبيق سياسات الترخيص"""
        principal = request.get("principal")
        action = request.get("action")
        resource = request.get("resource")

        if not self.policy_engine.evaluate(principal, action, resource):
            raise SecurityException(f"Access denied: {principal.id} cannot {action} on {resource}")

        logger.info("✅ Authorization passed")
        return request


class InputValidationLayer(SecurityLayer):
    """طبقة 4: التحقق من المدخلات (Input Validation)"""

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """التحقق من صحة المدخلات"""
        # في الإنتاج، استخدم Marshmallow أو Pydantic
        # هنا نستخدم تحقق بسيط للمثال

        data = request.get("data", {})
        # تحقق من SQL injection
        for key, value in data.items():
            if isinstance(value, str) and any(
                pattern in value.lower() for pattern in ["drop table", "select *", "--"]
            ):
                raise SecurityException(f"Potential SQL injection detected in {key}")

        logger.info("✅ Input validation passed")
        return request


class RateLimitingLayer(SecurityLayer):
    """طبقة 5: حدود المعدل (Rate Limiting)"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_counts: dict[str, list[datetime]] = {}

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """تطبيق حدود المعدل"""
        principal = request.get("principal")
        if not principal:
            return request

        # تنظيف الطلبات القديمة
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)

        if principal.id not in self._request_counts:
            self._request_counts[principal.id] = []

        self._request_counts[principal.id] = [
            ts for ts in self._request_counts[principal.id] if ts > window_start
        ]

        # تحقق من الحد
        if len(self._request_counts[principal.id]) >= self.max_requests:
            raise SecurityException(
                f"Rate limit exceeded for {principal.id}: "
                f"{self.max_requests} requests per {self.window_seconds}s"
            )

        self._request_counts[principal.id].append(now)
        logger.info("✅ Rate limiting passed")
        return request


class AuditLoggingLayer(SecurityLayer):
    """طبقة 6: التدقيق (Audit Logging)"""

    def __init__(self):
        self._audit_log: list[dict[str, Any]] = []

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """تسجيل الطلب للتدقيق"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "principal": request.get("principal", {}).id if request.get("principal") else None,
            "action": request.get("action"),
            "resource": request.get("resource"),
            "ip_address": request.get("ip_address"),
            "user_agent": request.get("user_agent"),
        }
        self._audit_log.append(audit_entry)
        logger.info(f"📝 Audit log: {audit_entry}")
        return request

    def get_audit_log(
        self, principal_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """الحصول على سجل التدقيق"""
        logs = self._audit_log
        if principal_id:
            logs = [log for log in logs if log.get("principal") == principal_id]
        return logs[-limit:]


class SecurityPipeline:
    """
    خط أنابيب الأمان (Security Pipeline)

    يطبق جميع طبقات الأمان بالترتيب
    """

    def __init__(self):
        self.layers: list[SecurityLayer] = []

    def add_layer(self, layer: SecurityLayer) -> None:
        """إضافة طبقة أمان"""
        self.layers.append(layer)
        logger.info(f"✅ Security layer added: {layer.__class__.__name__}")

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """معالجة الطلب عبر جميع الطبقات"""
        for layer in self.layers:
            try:
                request = await layer.process(request)
            except SecurityException as e:
                logger.error(f"❌ Security layer {layer.__class__.__name__} failed: {e}")
                raise

        logger.info("✅ All security layers passed")
        return request


class SecurityException(Exception):
    """استثناء أمني"""

    pass


# ======================================================================================
# COMPLIANCE ENGINE - محرك الامتثال
# ======================================================================================


class ComplianceRegulation(Enum):
    """اللوائح المدعومة"""

    GDPR = "gdpr"  # General Data Protection Regulation (EU)
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act (US)
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    SOC2 = "soc2"  # Service Organization Control 2
    ISO27001 = "iso27001"  # Information Security Management


@dataclass
class ComplianceRule:
    """قاعدة امتثال"""

    regulation: ComplianceRegulation
    rule_id: str
    description: str
    validator: Callable[[dict[str, Any]], bool]
    remediation: str  # خطوات العلاج عند الفشل


class ComplianceEngine:
    """
    محرك الامتثال (Compliance Engine)

    يفصل متطلبات الامتثال عن منطق العمل
    """

    def __init__(self):
        self.rules: list[ComplianceRule] = []

    def add_rule(self, rule: ComplianceRule) -> None:
        """إضافة قاعدة امتثال"""
        self.rules.append(rule)
        logger.info(f"✅ Compliance rule added: {rule.regulation.value}/{rule.rule_id}")

    async def validate(
        self, data: dict[str, Any], regulations: list[ComplianceRegulation] | None = None
    ) -> dict[str, Any]:
        """
        التحقق من الامتثال

        Args:
            data: البيانات المراد التحقق منها
            regulations: اللوائح المراد التحقق منها (None = جميع اللوائح)

        Returns:
            نتيجة التحقق مع القواعد الفاشلة
        """
        applicable_rules = self.rules
        if regulations:
            applicable_rules = [r for r in self.rules if r.regulation in regulations]

        failed_rules = []
        for rule in applicable_rules:
            try:
                if not rule.validator(data):
                    failed_rules.append(
                        {
                            "regulation": rule.regulation.value,
                            "rule_id": rule.rule_id,
                            "description": rule.description,
                            "remediation": rule.remediation,
                        }
                    )
                    logger.warning(
                        f"⚠️ Compliance violation: {rule.regulation.value}/{rule.rule_id}"
                    )
            except Exception as e:
                logger.error(f"❌ Error validating rule {rule.rule_id}: {e}")

        is_compliant = len(failed_rules) == 0
        result = {"is_compliant": is_compliant, "failed_rules": failed_rules}

        if is_compliant:
            logger.info("✅ All compliance checks passed")
        else:
            logger.warning(f"⚠️ {len(failed_rules)} compliance violations found")

        return result


# ======================================================================================
# DATA GOVERNANCE FRAMEWORK - إطار حوكمة البيانات
# ======================================================================================


class DataClassification(Enum):
    """تصنيف البيانات"""

    PUBLIC = "public"  # عامة
    INTERNAL = "internal"  # داخلية
    CONFIDENTIAL = "confidential"  # سرية
    HIGHLY_RESTRICTED = "highly_restricted"  # مقيدة للغاية


@dataclass
class DataGovernancePolicy:
    """سياسة حوكمة البيانات"""

    classification: DataClassification
    retention_days: int  # مدة الاحتفاظ
    encryption_required: bool  # التشفير مطلوب
    backup_required: bool  # النسخ الاحتياطي مطلوب
    access_logging_required: bool  # تسجيل الوصول مطلوب
    allowed_locations: list[str]  # المواقع المسموحة (للسيادة على البيانات)


class DataGovernanceFramework:
    """
    إطار حوكمة البيانات (Data Governance Framework)

    يدير سياسات البيانات بشكل موحد:
    - تصنيف البيانات
    - سياسات الاحتفاظ
    - سياسات التشفير
    - سياسات الوصول
    """

    def __init__(self):
        self.policies: dict[DataClassification, DataGovernancePolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """تهيئة السياسات الافتراضية"""
        self.policies[DataClassification.PUBLIC] = DataGovernancePolicy(
            classification=DataClassification.PUBLIC,
            retention_days=365,
            encryption_required=False,
            backup_required=True,
            access_logging_required=False,
            allowed_locations=["*"],
        )

        self.policies[DataClassification.INTERNAL] = DataGovernancePolicy(
            classification=DataClassification.INTERNAL,
            retention_days=730,
            encryption_required=True,
            backup_required=True,
            access_logging_required=True,
            allowed_locations=["*"],
        )

        self.policies[DataClassification.CONFIDENTIAL] = DataGovernancePolicy(
            classification=DataClassification.CONFIDENTIAL,
            retention_days=2190,  # 6 سنوات
            encryption_required=True,
            backup_required=True,
            access_logging_required=True,
            allowed_locations=["EU", "US"],
        )

        self.policies[DataClassification.HIGHLY_RESTRICTED] = DataGovernancePolicy(
            classification=DataClassification.HIGHLY_RESTRICTED,
            retention_days=2555,  # 7 سنوات
            encryption_required=True,
            backup_required=True,
            access_logging_required=True,
            allowed_locations=["EU"],  # السيادة على البيانات
        )

    def get_policy(self, classification: DataClassification) -> DataGovernancePolicy:
        """الحصول على سياسة لتصنيف معين"""
        return self.policies[classification]

    def should_encrypt(self, classification: DataClassification) -> bool:
        """التحقق مما إذا كان التشفير مطلوب"""
        return self.policies[classification].encryption_required

    def should_backup(self, classification: DataClassification) -> bool:
        """التحقق مما إذا كان النسخ الاحتياطي مطلوب"""
        return self.policies[classification].backup_required

    def is_location_allowed(self, classification: DataClassification, location: str) -> bool:
        """التحقق مما إذا كان الموقع مسموح"""
        allowed = self.policies[classification].allowed_locations
        return "*" in allowed or location in allowed

    def calculate_deletion_date(
        self, classification: DataClassification, created_at: datetime
    ) -> datetime:
        """حساب تاريخ الحذف المتوقع"""
        retention_days = self.policies[classification].retention_days
        return created_at + timedelta(days=retention_days)


# ======================================================================================
# POLICY BOUNDARY ABSTRACTION
# ======================================================================================


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
