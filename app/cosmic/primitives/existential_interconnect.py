# ======================================================================================
#  EXISTENTIAL INTERCONNECT (EI) - CORE EXISTENTIAL PRIMITIVE
# ======================================================================================
#  PURPOSE (الغرض):
#    وصلة الترابط الوجودي - معيار موحد لكيفية تفاعل المعلومات بين
#    الـ GCUs والأنظمة المختلفة. تضمن هذه الوصلة أن أي نقل للمعلومات
#    يتوافق مع سياسات xDLP ويترك بصمة Provenance وجودية تلقائياً.
#
#  KEY FEATURES (المميزات الرئيسية):
#    - نقل آمن للمعلومات بين الوحدات
#    - تتبع أصل البيانات (Data Provenance)
#    - ضمان امتثال xDLP تلقائياً
#    - تسجيل شامل لجميع التفاعلات
#    - كشف التشوهات الوجودية
#
#  DESIGN PRINCIPLES (مبادئ التصميم):
#    - الأمان بالتصميم (Security by design)
#    - الشفافية الكاملة (Complete transparency)
#    - القابلية للتدقيق (Full auditability)
# ======================================================================================

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


class InterconnectType(Enum):
    """نوع الترابط الوجودي"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    STREAMING = "streaming"
    BATCH = "batch"


class SecurityLevel(Enum):
    """مستوى الأمان"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    TOP_SECRET = "top_secret"


class InterconnectStatus(Enum):
    """حالة الترابط"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class ProvenanceRecord:
    """سجل أصل البيانات - تتبع رحلة المعلومات"""
    record_id: str
    source_consciousness_id: str
    target_consciousness_id: str
    timestamp: datetime
    data_hash: str
    security_level: SecurityLevel
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterconnectMetrics:
    """مقاييس أداء الترابط"""
    total_transfers: int = 0
    successful_transfers: int = 0
    failed_transfers: int = 0
    total_data_size_bytes: int = 0
    avg_transfer_time_ms: float = 0.0
    detected_anomalies: int = 0


class ExistentialInterconnect:
    """
    وصلة الترابط الوجودي (EI) - البنية التحتية للاتصال بين الوحدات
    
    توفر طبقة آمنة ومراقبة لنقل المعلومات بين وحدات الوعي المحكم (GCUs)
    مع ضمان الامتثال الكامل للبروتوكولات الوجودية وتسجيل شامل.
    
    Examples:
        >>> # إنشاء وصلة ترابط جديدة
        >>> ei = ExistentialInterconnect(
        ...     interconnect_type=InterconnectType.SYNCHRONOUS,
        ...     security_level=SecurityLevel.CONFIDENTIAL
        ... )
        >>> 
        >>> # نقل معلومات بين وحدتين
        >>> result = ei.transfer_information(
        ...     source_gcu_id="gcu-001",
        ...     target_gcu_id="gcu-002",
        ...     data={"message": "secure data"}
        ... )
    """
    
    def __init__(
        self,
        interconnect_type: InterconnectType = InterconnectType.SYNCHRONOUS,
        security_level: SecurityLevel = SecurityLevel.INTERNAL,
        enable_provenance_tracking: bool = True,
        enable_anomaly_detection: bool = True
    ):
        """
        تهيئة وصلة الترابط الوجودي
        
        Args:
            interconnect_type: نوع الترابط
            security_level: مستوى الأمان الافتراضي
            enable_provenance_tracking: تفعيل تتبع أصل البيانات
            enable_anomaly_detection: تفعيل كشف التشوهات
        """
        self.interconnect_id = str(uuid.uuid4())
        self.interconnect_type = interconnect_type
        self.security_level = security_level
        self.status = InterconnectStatus.ACTIVE
        
        # إعدادات التتبع والمراقبة
        self.enable_provenance_tracking = enable_provenance_tracking
        self.enable_anomaly_detection = enable_anomaly_detection
        
        # سجل أصل البيانات
        self.provenance_records: List[ProvenanceRecord] = []
        
        # مقاييس الأداء
        self.metrics = InterconnectMetrics()
        
        # الطابع الزمني
        self.created_at = datetime.now(UTC)
        self.last_transfer_at: Optional[datetime] = None
        
        # سجل التشوهات المكتشفة
        self.anomalies: List[Dict[str, Any]] = []
    
    def transfer_information(
        self,
        source_gcu_id: str,
        target_gcu_id: str,
        data: Dict[str, Any],
        security_level: Optional[SecurityLevel] = None,
        validate_integrity: bool = True
    ) -> Dict[str, Any]:
        """
        نقل معلومات بشكل آمن بين وحدتي وعي
        
        Args:
            source_gcu_id: معرف وحدة المصدر
            target_gcu_id: معرف وحدة الهدف
            data: البيانات المراد نقلها
            security_level: مستوى أمان مخصص (اختياري)
            validate_integrity: التحقق من نزاهة البيانات
            
        Returns:
            نتيجة عملية النقل مع البيانات الوصفية
        """
        if self.status != InterconnectStatus.ACTIVE:
            return {
                "success": False,
                "error": f"Interconnect is {self.status.value}",
                "interconnect_id": self.interconnect_id
            }
        
        start_time = datetime.now(UTC)
        transfer_security_level = security_level or self.security_level
        
        try:
            # التحقق من نزاهة البيانات
            if validate_integrity:
                integrity_check = self._validate_data_integrity(data)
                if not integrity_check["valid"]:
                    self.metrics.failed_transfers += 1
                    return {
                        "success": False,
                        "error": "Data integrity validation failed",
                        "details": integrity_check
                    }
            
            # تطبيق سياسات xDLP
            dlp_check = self._apply_dlp_policies(data, transfer_security_level)
            if not dlp_check["compliant"]:
                self.metrics.failed_transfers += 1
                return {
                    "success": False,
                    "error": "DLP policy violation",
                    "violations": dlp_check["violations"]
                }
            
            # إنشاء بصمة وجودية للبيانات
            data_signature = self._create_data_signature(data, source_gcu_id, target_gcu_id)
            
            # تسجيل سجل أصل البيانات
            if self.enable_provenance_tracking:
                provenance = self._record_provenance(
                    source_gcu_id,
                    target_gcu_id,
                    data,
                    transfer_security_level
                )
            
            # كشف التشوهات
            if self.enable_anomaly_detection:
                anomaly_detected = self._detect_anomalies(data, source_gcu_id, target_gcu_id)
                if anomaly_detected:
                    self.metrics.detected_anomalies += 1
            
            # تحديث المقاييس
            self.metrics.total_transfers += 1
            self.metrics.successful_transfers += 1
            self.metrics.total_data_size_bytes += len(str(data).encode())
            
            transfer_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            self._update_avg_transfer_time(transfer_time)
            
            self.last_transfer_at = datetime.now(UTC)
            
            return {
                "success": True,
                "interconnect_id": self.interconnect_id,
                "transfer_id": str(uuid.uuid4()),
                "source_gcu_id": source_gcu_id,
                "target_gcu_id": target_gcu_id,
                "data_signature": data_signature,
                "provenance_record_id": provenance.record_id if self.enable_provenance_tracking else None,
                "security_level": transfer_security_level.value,
                "transfer_time_ms": transfer_time,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            self.metrics.failed_transfers += 1
            return {
                "success": False,
                "error": str(e),
                "interconnect_id": self.interconnect_id
            }
    
    def get_provenance_chain(
        self,
        consciousness_id: str,
        max_depth: int = 10
    ) -> List[ProvenanceRecord]:
        """
        الحصول على سلسلة أصل البيانات لوحدة وعي محددة
        
        Args:
            consciousness_id: معرف وحدة الوعي
            max_depth: أقصى عمق للبحث
            
        Returns:
            قائمة بسجلات الأصل
        """
        chain = []
        for record in self.provenance_records[-max_depth:]:
            if (record.source_consciousness_id == consciousness_id or
                record.target_consciousness_id == consciousness_id):
                chain.append(record)
        return chain
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        الحصول على تقرير صحة الترابط
        
        Returns:
            تقرير شامل بحالة الترابط
        """
        success_rate = 0.0
        if self.metrics.total_transfers > 0:
            success_rate = (
                self.metrics.successful_transfers /
                self.metrics.total_transfers
            ) * 100
        
        return {
            "interconnect_id": self.interconnect_id,
            "interconnect_type": self.interconnect_type.value,
            "status": self.status.value,
            "security_level": self.security_level.value,
            "created_at": self.created_at.isoformat(),
            "last_transfer_at": self.last_transfer_at.isoformat() if self.last_transfer_at else None,
            "metrics": {
                "total_transfers": self.metrics.total_transfers,
                "successful_transfers": self.metrics.successful_transfers,
                "failed_transfers": self.metrics.failed_transfers,
                "success_rate": f"{success_rate:.2f}%",
                "total_data_size_bytes": self.metrics.total_data_size_bytes,
                "avg_transfer_time_ms": f"{self.metrics.avg_transfer_time_ms:.2f}",
                "detected_anomalies": self.metrics.detected_anomalies
            },
            "provenance_records_count": len(self.provenance_records),
            "features": {
                "provenance_tracking": self.enable_provenance_tracking,
                "anomaly_detection": self.enable_anomaly_detection
            }
        }
    
    def suspend(self) -> None:
        """تعليق الترابط"""
        self.status = InterconnectStatus.SUSPENDED
    
    def resume(self) -> None:
        """استئناف الترابط"""
        self.status = InterconnectStatus.ACTIVE
    
    def terminate(self) -> None:
        """إنهاء الترابط"""
        self.status = InterconnectStatus.TERMINATED
    
    def _validate_data_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        التحقق من نزاهة البيانات
        
        Args:
            data: البيانات المراد التحقق منها
            
        Returns:
            نتيجة التحقق
        """
        # تحقق بسيط - يمكن توسيعه
        try:
            data_hash = hashlib.sha256(str(data).encode()).hexdigest()
            return {
                "valid": True,
                "data_hash": data_hash
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _apply_dlp_policies(
        self,
        data: Dict[str, Any],
        security_level: SecurityLevel
    ) -> Dict[str, Any]:
        """
        تطبيق سياسات منع فقدان البيانات (DLP)
        
        Args:
            data: البيانات المراد فحصها
            security_level: مستوى الأمان
            
        Returns:
            نتيجة الفحص
        """
        violations = []
        
        # فحص البيانات الحساسة
        data_str = str(data).lower()
        
        # كلمات مفتاحية حساسة (يمكن توسيعها)
        sensitive_patterns = {
            SecurityLevel.TOP_SECRET: ["password", "secret", "api_key", "token"],
            SecurityLevel.CONFIDENTIAL: ["credit_card", "ssn", "private"],
            SecurityLevel.INTERNAL: ["internal_only", "confidential"]
        }
        
        # التحقق بناءً على مستوى الأمان
        for level, patterns in sensitive_patterns.items():
            if security_level.value >= level.value:
                continue
            for pattern in patterns:
                if pattern in data_str:
                    violations.append(f"Sensitive pattern '{pattern}' found in data")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "security_level": security_level.value
        }
    
    def _create_data_signature(
        self,
        data: Dict[str, Any],
        source_id: str,
        target_id: str
    ) -> str:
        """
        إنشاء بصمة وجودية للبيانات
        
        Args:
            data: البيانات
            source_id: معرف المصدر
            target_id: معرف الهدف
            
        Returns:
            البصمة التشفيرية
        """
        signature_data = f"{source_id}:{target_id}:{str(data)}:{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def _record_provenance(
        self,
        source_id: str,
        target_id: str,
        data: Dict[str, Any],
        security_level: SecurityLevel
    ) -> ProvenanceRecord:
        """
        تسجيل سجل أصل البيانات
        
        Args:
            source_id: معرف المصدر
            target_id: معرف الهدف
            data: البيانات
            security_level: مستوى الأمان
            
        Returns:
            سجل الأصل
        """
        data_hash = hashlib.sha256(str(data).encode()).hexdigest()
        
        record = ProvenanceRecord(
            record_id=str(uuid.uuid4()),
            source_consciousness_id=source_id,
            target_consciousness_id=target_id,
            timestamp=datetime.now(UTC),
            data_hash=data_hash,
            security_level=security_level,
            metadata={
                "interconnect_id": self.interconnect_id,
                "interconnect_type": self.interconnect_type.value
            }
        )
        
        self.provenance_records.append(record)
        return record
    
    def _detect_anomalies(
        self,
        data: Dict[str, Any],
        source_id: str,
        target_id: str
    ) -> bool:
        """
        كشف التشوهات الوجودية في عملية النقل
        
        Args:
            data: البيانات
            source_id: معرف المصدر
            target_id: معرف الهدف
            
        Returns:
            True إذا تم اكتشاف تشوه
        """
        # كشف بسيط للتشوهات (يمكن توسيعه بخوارزميات ML)
        anomaly_detected = False
        
        # حجم البيانات غير طبيعي
        data_size = len(str(data).encode())
        if data_size > 1000000:  # أكثر من 1MB
            self.anomalies.append({
                "type": "large_data_size",
                "size": data_size,
                "source_id": source_id,
                "target_id": target_id,
                "timestamp": datetime.now(UTC).isoformat()
            })
            anomaly_detected = True
        
        # نقل متكرر من نفس المصدر
        recent_transfers = [
            r for r in self.provenance_records[-10:]
            if r.source_consciousness_id == source_id
        ]
        if len(recent_transfers) > 5:
            self.anomalies.append({
                "type": "high_frequency_transfer",
                "count": len(recent_transfers),
                "source_id": source_id,
                "timestamp": datetime.now(UTC).isoformat()
            })
            anomaly_detected = True
        
        return anomaly_detected
    
    def _update_avg_transfer_time(self, new_time: float) -> None:
        """
        تحديث متوسط وقت النقل
        
        Args:
            new_time: الوقت الجديد بالميلي ثانية
        """
        total_transfers = self.metrics.total_transfers
        current_avg = self.metrics.avg_transfer_time_ms
        
        if total_transfers > 0:
            new_avg = ((current_avg * (total_transfers - 1)) + new_time) / total_transfers
            self.metrics.avg_transfer_time_ms = new_avg
    
    def __repr__(self) -> str:
        return (
            f"ExistentialInterconnect("
            f"interconnect_id='{self.interconnect_id}', "
            f"type={self.interconnect_type.value}, "
            f"security_level={self.security_level.value}, "
            f"status={self.status.value})"
        )
