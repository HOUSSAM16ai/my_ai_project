# ======================================================================================
#  EXISTENTIAL PROTOCOL PACKAGE (EPP) - CORE EXISTENTIAL PRIMITIVE
# ======================================================================================
#  PURPOSE (الغرض):
#    حزمة البروتوكول الوجودي - مجموعة مسبقة التحديد من السياسات والقواعد
#    الوجودية (مثلاً، بروتوكول السرية، بروتوكول المشاركة، بروتوكول التعديل).
#    يمكن للـ GCU "الاشتراك" في هذه الحزم بشكل موحد.
#
#  KEY FEATURES (المميزات الرئيسية):
#    - بروتوكولات معدة مسبقاً وجاهزة للاستخدام
#    - قابلية للتخصيص والتوسع
#    - إدارة تلقائية للسياسات
#    - تطبيق موحد عبر جميع الأنظمة
#
#  DESIGN PRINCIPLES (مبادئ التصميم):
#    - التعريف مرة واحدة، الاستخدام في كل مكان
#    - البساطة في التطبيق
#    - المرونة في التخصيص
# ======================================================================================

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from dataclasses import dataclass, field


class ProtocolType(Enum):
    """أنواع البروتوكولات الوجودية"""
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"
    SHARING = "sharing"
    MODIFICATION = "modification"
    DELETION = "deletion"
    AUDIT = "audit"
    COMPLIANCE = "compliance"


class ProtocolSeverity(Enum):
    """مستوى خطورة انتهاك البروتوكول"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PolicyRule:
    """قاعدة سياسة ضمن البروتوكول"""
    rule_id: str
    name: str
    description: str
    severity: ProtocolSeverity
    validator: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtocolViolation:
    """سجل انتهاك للبروتوكول"""
    violation_id: str
    protocol_name: str
    rule_id: str
    severity: ProtocolSeverity
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExistentialProtocolPackage:
    """
    حزمة البروتوكول الوجودي (EPP) - مجموعة منظمة من السياسات والقواعد
    
    توفر بروتوكولات معدة مسبقاً يمكن للـ GCUs الاشتراك فيها بشكل موحد،
    مع إدارة تلقائية للسياسات والتحقق من الامتثال.
    
    Examples:
        >>> # إنشاء حزمة بروتوكول السرية
        >>> confidentiality_epp = ExistentialProtocolPackage(
        ...     protocol_type=ProtocolType.CONFIDENTIALITY,
        ...     name="High Security Confidentiality",
        ...     description="Maximum data protection protocol"
        ... )
        >>> 
        >>> # إضافة قاعدة مخصصة
        >>> confidentiality_epp.add_policy_rule(
        ...     name="Encryption Required",
        ...     description="All data must be encrypted",
        ...     severity=ProtocolSeverity.CRITICAL
        ... )
        >>> 
        >>> # التحقق من البيانات
        >>> result = confidentiality_epp.validate_data({"sensitive": "data"})
    """
    
    def __init__(
        self,
        protocol_type: ProtocolType,
        name: str,
        description: str,
        version: str = "1.0.0",
        auto_apply: bool = True
    ):
        """
        تهيئة حزمة البروتوكول الوجودي
        
        Args:
            protocol_type: نوع البروتوكول
            name: اسم الحزمة
            description: وصف الحزمة
            version: إصدار البروتوكول
            auto_apply: تطبيق تلقائي للقواعد
        """
        self.protocol_id = str(uuid.uuid4())
        self.protocol_type = protocol_type
        self.name = name
        self.description = description
        self.version = version
        self.auto_apply = auto_apply
        
        # القواعد المضمنة في البروتوكول
        self.policy_rules: List[PolicyRule] = []
        
        # سجل الانتهاكات
        self.violations: List[ProtocolViolation] = []
        
        # إحصائيات التطبيق
        self.application_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "total_violations": 0
        }
        
        # الطابع الزمني
        self.created_at = datetime.now(UTC)
        self.last_updated_at = self.created_at
        
        # تحميل القواعد الافتراضية حسب النوع
        self._load_default_rules()
    
    def add_policy_rule(
        self,
        name: str,
        description: str,
        severity: ProtocolSeverity,
        validator: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PolicyRule:
        """
        إضافة قاعدة سياسة جديدة
        
        Args:
            name: اسم القاعدة
            description: وصف القاعدة
            severity: مستوى الخطورة
            validator: دالة التحقق (اختياري)
            metadata: بيانات وصفية إضافية
            
        Returns:
            القاعدة المضافة
        """
        rule = PolicyRule(
            rule_id=str(uuid.uuid4()),
            name=name,
            description=description,
            severity=severity,
            validator=validator,
            metadata=metadata or {}
        )
        
        self.policy_rules.append(rule)
        self.last_updated_at = datetime.now(UTC)
        
        return rule
    
    def remove_policy_rule(self, rule_id: str) -> bool:
        """
        إزالة قاعدة سياسة
        
        Args:
            rule_id: معرف القاعدة
            
        Returns:
            True إذا نجحت الإزالة
        """
        for i, rule in enumerate(self.policy_rules):
            if rule.rule_id == rule_id:
                self.policy_rules.pop(i)
                self.last_updated_at = datetime.now(UTC)
                return True
        return False
    
    def validate_data(
        self,
        data: Dict[str, Any],
        strict_mode: bool = True
    ) -> Dict[str, Any]:
        """
        التحقق من البيانات وفقاً لقواعد البروتوكول
        
        Args:
            data: البيانات المراد التحقق منها
            strict_mode: الوضع الصارم (يفشل عند أول انتهاك)
            
        Returns:
            نتيجة التحقق مع أي انتهاكات
        """
        self.application_stats["total_validations"] += 1
        
        violations_found = []
        
        for rule in self.policy_rules:
            violation = self._check_rule(rule, data)
            
            if violation:
                violations_found.append(violation)
                
                # في الوضع الصارم، نتوقف عند أول انتهاك حرج
                if strict_mode and rule.severity == ProtocolSeverity.CRITICAL:
                    self.application_stats["failed_validations"] += 1
                    return {
                        "valid": False,
                        "protocol_id": self.protocol_id,
                        "protocol_name": self.name,
                        "violations": violations_found,
                        "strict_mode": True
                    }
        
        # تحديث الإحصائيات
        if violations_found:
            self.application_stats["failed_validations"] += 1
            self.application_stats["total_violations"] += len(violations_found)
        else:
            self.application_stats["successful_validations"] += 1
        
        return {
            "valid": len(violations_found) == 0,
            "protocol_id": self.protocol_id,
            "protocol_name": self.name,
            "violations": violations_found,
            "strict_mode": strict_mode
        }
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """
        الحصول على تقرير الامتثال الشامل
        
        Returns:
            تقرير بالإحصائيات والانتهاكات
        """
        compliance_rate = 0.0
        if self.application_stats["total_validations"] > 0:
            compliance_rate = (
                self.application_stats["successful_validations"] /
                self.application_stats["total_validations"]
            ) * 100
        
        # تجميع الانتهاكات حسب الخطورة
        violations_by_severity = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for violation in self.violations:
            violations_by_severity[violation.severity.value] += 1
        
        return {
            "protocol_id": self.protocol_id,
            "protocol_name": self.name,
            "protocol_type": self.protocol_type.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "last_updated_at": self.last_updated_at.isoformat(),
            "statistics": {
                **self.application_stats,
                "compliance_rate": f"{compliance_rate:.2f}%"
            },
            "violations_by_severity": violations_by_severity,
            "total_rules": len(self.policy_rules),
            "auto_apply": self.auto_apply
        }
    
    def get_rules_summary(self) -> List[Dict[str, Any]]:
        """
        الحصول على ملخص القواعد
        
        Returns:
            قائمة بملخصات القواعد
        """
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "severity": rule.severity.value,
                "has_custom_validator": rule.validator is not None
            }
            for rule in self.policy_rules
        ]
    
    def _load_default_rules(self) -> None:
        """تحميل القواعد الافتراضية حسب نوع البروتوكول"""
        
        if self.protocol_type == ProtocolType.CONFIDENTIALITY:
            self._load_confidentiality_rules()
        elif self.protocol_type == ProtocolType.INTEGRITY:
            self._load_integrity_rules()
        elif self.protocol_type == ProtocolType.AVAILABILITY:
            self._load_availability_rules()
        elif self.protocol_type == ProtocolType.SHARING:
            self._load_sharing_rules()
        elif self.protocol_type == ProtocolType.MODIFICATION:
            self._load_modification_rules()
        elif self.protocol_type == ProtocolType.AUDIT:
            self._load_audit_rules()
        elif self.protocol_type == ProtocolType.COMPLIANCE:
            self._load_compliance_rules()
    
    def _load_confidentiality_rules(self) -> None:
        """تحميل قواعد السرية"""
        self.add_policy_rule(
            name="Data Encryption Required",
            description="All sensitive data must be encrypted",
            severity=ProtocolSeverity.CRITICAL,
            validator=lambda data: "encrypted" in data or "encryption_applied" in data
        )
        
        self.add_policy_rule(
            name="Access Control",
            description="Data must have access control metadata",
            severity=ProtocolSeverity.ERROR,
            validator=lambda data: "access_control" in data or "permissions" in data
        )
    
    def _load_integrity_rules(self) -> None:
        """تحميل قواعد النزاهة"""
        self.add_policy_rule(
            name="Data Checksum Required",
            description="Data must include checksum for integrity verification",
            severity=ProtocolSeverity.CRITICAL,
            validator=lambda data: "checksum" in data or "hash" in data
        )
        
        self.add_policy_rule(
            name="Timestamp Required",
            description="Data must include timestamp",
            severity=ProtocolSeverity.WARNING,
            validator=lambda data: "timestamp" in data or "created_at" in data
        )
    
    def _load_availability_rules(self) -> None:
        """تحميل قواعد التوافر"""
        self.add_policy_rule(
            name="Redundancy Metadata",
            description="Data must include redundancy information",
            severity=ProtocolSeverity.WARNING,
            validator=lambda data: "replica_count" in data or "backup_location" in data
        )
    
    def _load_sharing_rules(self) -> None:
        """تحميل قواعد المشاركة"""
        self.add_policy_rule(
            name="Sharing Permissions",
            description="Data must specify sharing permissions",
            severity=ProtocolSeverity.ERROR,
            validator=lambda data: "share_with" in data or "sharing_policy" in data
        )
    
    def _load_modification_rules(self) -> None:
        """تحميل قواعد التعديل"""
        self.add_policy_rule(
            name="Modification Tracking",
            description="Modifications must be tracked",
            severity=ProtocolSeverity.WARNING,
            validator=lambda data: "modified_by" in data or "modification_log" in data
        )
    
    def _load_audit_rules(self) -> None:
        """تحميل قواعد التدقيق"""
        self.add_policy_rule(
            name="Audit Trail Required",
            description="All operations must have audit trail",
            severity=ProtocolSeverity.CRITICAL,
            validator=lambda data: "audit_log" in data or "operation_id" in data
        )
    
    def _load_compliance_rules(self) -> None:
        """تحميل قواعد الامتثال"""
        self.add_policy_rule(
            name="Compliance Metadata",
            description="Data must include compliance metadata",
            severity=ProtocolSeverity.ERROR,
            validator=lambda data: "compliance_tags" in data or "regulation" in data
        )
    
    def _check_rule(
        self,
        rule: PolicyRule,
        data: Dict[str, Any]
    ) -> Optional[ProtocolViolation]:
        """
        التحقق من قاعدة واحدة
        
        Args:
            rule: القاعدة المراد التحقق منها
            data: البيانات
            
        Returns:
            انتهاك إن وُجد
        """
        try:
            # إذا كان لدينا validator مخصص، نستخدمه
            if rule.validator:
                is_valid = rule.validator(data)
                if not is_valid:
                    return self._create_violation(rule, "Custom validator failed")
            
            # التحقق الافتراضي - نتحقق من وجود المفاتيح المطلوبة
            # (هذا مثال بسيط، يمكن توسيعه)
            
            return None
            
        except Exception as e:
            # في حالة فشل التحقق، نسجل انتهاك
            return self._create_violation(
                rule,
                f"Validation error: {str(e)}"
            )
    
    def _create_violation(
        self,
        rule: PolicyRule,
        description: str
    ) -> ProtocolViolation:
        """
        إنشاء سجل انتهاك
        
        Args:
            rule: القاعدة المنتهكة
            description: وصف الانتهاك
            
        Returns:
            سجل الانتهاك
        """
        violation = ProtocolViolation(
            violation_id=str(uuid.uuid4()),
            protocol_name=self.name,
            rule_id=rule.rule_id,
            severity=rule.severity,
            description=description,
            timestamp=datetime.now(UTC),
            metadata={
                "rule_name": rule.name,
                "protocol_id": self.protocol_id
            }
        )
        
        self.violations.append(violation)
        return violation
    
    def __repr__(self) -> str:
        return (
            f"ExistentialProtocolPackage("
            f"protocol_id='{self.protocol_id}', "
            f"name='{self.name}', "
            f"type={self.protocol_type.value}, "
            f"version={self.version})"
        )


# ======================================================================================
# PROTOCOL FACTORY - مصنع البروتوكولات الجاهزة
# ======================================================================================

class ProtocolFactory:
    """
    مصنع لإنشاء بروتوكولات معدة مسبقاً
    
    يوفر طريقة سريعة لإنشاء البروتوكولات الشائعة بإعدادات محسنة.
    """
    
    @staticmethod
    def create_high_security_package() -> ExistentialProtocolPackage:
        """إنشاء حزمة أمان عالي"""
        return ExistentialProtocolPackage(
            protocol_type=ProtocolType.CONFIDENTIALITY,
            name="High Security Package",
            description="Maximum security protocol for sensitive data",
            version="1.0.0"
        )
    
    @staticmethod
    def create_data_integrity_package() -> ExistentialProtocolPackage:
        """إنشاء حزمة نزاهة البيانات"""
        return ExistentialProtocolPackage(
            protocol_type=ProtocolType.INTEGRITY,
            name="Data Integrity Package",
            description="Ensures data integrity and consistency",
            version="1.0.0"
        )
    
    @staticmethod
    def create_audit_compliance_package() -> ExistentialProtocolPackage:
        """إنشاء حزمة التدقيق والامتثال"""
        return ExistentialProtocolPackage(
            protocol_type=ProtocolType.AUDIT,
            name="Audit & Compliance Package",
            description="Complete audit trail and compliance tracking",
            version="1.0.0"
        )
    
    @staticmethod
    def create_custom_package(
        protocol_type: ProtocolType,
        name: str,
        description: str
    ) -> ExistentialProtocolPackage:
        """إنشاء حزمة مخصصة"""
        return ExistentialProtocolPackage(
            protocol_type=protocol_type,
            name=name,
            description=description,
            version="1.0.0"
        )
