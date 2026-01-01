"""Policy Engine - Policy evaluation and enforcement engine."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

from .auth import Principal

logger = logging.getLogger(__name__)

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

    # TODO: Split this function (49 lines) - KISS principle
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

    # TODO: Reduce parameters (6 params) - Use config object
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
        return self._evaluate_conditions(principal, resource, rule.conditions, context)

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
            elif principal_pattern == principal.id or principal_pattern == "*":
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
# TODO: Split this function (43 lines) - KISS principle

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
        if operator == "!=":
            return str(actual_value) != value
        if operator == ">":
            return float(actual_value) > float(value)
        if operator == "<":
            return float(actual_value) < float(value)
        if operator == ">=":
            return float(actual_value) >= float(value)
        if operator == "<=":
            return float(actual_value) <= float(value)

        return False
