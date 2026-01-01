"""Policy Compliance - Compliance and regulatory policies."""
from __future__ import annotations

from typing import Any

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

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
