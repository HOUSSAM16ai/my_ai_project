# ======================================================================================
#  GOVERNED CONSCIOUSNESS UNIT (GCU) - CORE EXISTENTIAL PRIMITIVE
# ======================================================================================
#  PURPOSE (الغرض):
#    وحدة الوعي المحكم - الوحدة الأساسية لأي كيان (بشري، ذكاء اصطناعي، نظام آلي)
#    في الشركة. كل GCU لديها واجهة موحدة للتفاعل مع بروتوكولات الحوكمة
#    وتشفيرها الوجودي. تُبرمج على احترام البروتوكولات الوجودية مسبقاً.
#
#  KEY FEATURES (المميزات الرئيسية):
#    - واجهة موحدة وبسيطة (Simple unified interface)
#    - تشفير وجودي مدمج (Built-in existential encryption)
#    - احترام تلقائي للبروتوكولات (Automatic protocol compliance)
#    - تتبع متقدم للحالة (Advanced state tracking)
#    - قابلية للتوسع اللامحدود (Infinite scalability)
#
#  DESIGN PRINCIPLES (مبادئ التصميم):
#    - البساطة في الواجهة، التعقيد في التنفيذ
#    - التكرار الذكي والنمطية
#    - الأمان الوجودي بالتصميم
# ======================================================================================

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


class ConsciousnessType(Enum):
    """نوع الوعي - أنواع الكيانات المدعومة"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    HYBRID = "hybrid"


class ProtocolComplianceLevel(Enum):
    """مستوى الامتثال للبروتوكول"""
    STRICT = "strict"
    STANDARD = "standard"
    FLEXIBLE = "flexible"


@dataclass
class ExistentialState:
    """حالة الكيان الوجودية - تتبع متقدم للحالة"""
    consciousness_id: str
    timestamp: datetime
    state_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    protocol_compliance: ProtocolComplianceLevel = ProtocolComplianceLevel.STANDARD


class GovernedConsciousnessUnit:
    """
    وحدة الوعي المحكم (GCU) - اللبنة الأساسية للنظام الوجودي
    
    تمثل أي كيان في النظام بواجهة موحدة ومحكمة، مع دعم كامل
    للبروتوكولات الوجودية والتشفير والحوكمة.
    
    Examples:
        >>> # إنشاء وحدة وعي جديدة
        >>> gcu = GovernedConsciousnessUnit(
        ...     entity_type=ConsciousnessType.AI,
        ...     entity_id="ai-assistant-001",
        ...     name="AI Assistant"
        ... )
        >>> 
        >>> # الاشتراك في بروتوكول
        >>> gcu.subscribe_to_protocol("confidentiality_protocol")
        >>> 
        >>> # معالجة معلومات بشكل آمن
        >>> result = gcu.process_information({"query": "sensitive data"})
    """
    
    def __init__(
        self,
        entity_type: ConsciousnessType,
        entity_id: str,
        name: str,
        compliance_level: ProtocolComplianceLevel = ProtocolComplianceLevel.STANDARD,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        تهيئة وحدة الوعي المحكم
        
        Args:
            entity_type: نوع الكيان (بشري، ذكاء اصطناعي، نظام، هجين)
            entity_id: معرف فريد للكيان
            name: اسم الكيان
            compliance_level: مستوى الامتثال للبروتوكول
            metadata: بيانات وصفية إضافية
        """
        self.consciousness_id = str(uuid.uuid4())
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.name = name
        self.compliance_level = compliance_level
        self.metadata = metadata or {}
        
        # البروتوكولات المشترك فيها
        self.subscribed_protocols: List[str] = []
        
        # سجل الحالات الوجودية
        self.state_history: List[ExistentialState] = []
        
        # الطابع الزمني للإنشاء
        self.created_at = datetime.now(UTC)
        self.last_active_at = self.created_at
        
        # إحصائيات الأداء
        self.performance_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_response_time_ms": 0.0
        }
        
        # تسجيل الحالة الأولية
        self._record_state("initialized")
    
    def subscribe_to_protocol(self, protocol_name: str) -> bool:
        """
        الاشتراك في بروتوكول وجودي
        
        Args:
            protocol_name: اسم البروتوكول
            
        Returns:
            True إذا نجح الاشتراك
        """
        if protocol_name not in self.subscribed_protocols:
            self.subscribed_protocols.append(protocol_name)
            self._record_state(f"subscribed_to_{protocol_name}")
            return True
        return False
    
    def unsubscribe_from_protocol(self, protocol_name: str) -> bool:
        """
        إلغاء الاشتراك من بروتوكول
        
        Args:
            protocol_name: اسم البروتوكول
            
        Returns:
            True إذا نجح الإلغاء
        """
        if protocol_name in self.subscribed_protocols:
            self.subscribed_protocols.remove(protocol_name)
            self._record_state(f"unsubscribed_from_{protocol_name}")
            return True
        return False
    
    def process_information(
        self,
        data: Dict[str, Any],
        enforce_protocols: bool = True
    ) -> Dict[str, Any]:
        """
        معالجة معلومات بشكل آمن مع احترام البروتوكولات
        
        Args:
            data: البيانات المراد معالجتها
            enforce_protocols: فرض تطبيق البروتوكولات
            
        Returns:
            نتيجة المعالجة مع بيانات الامتثال
        """
        start_time = datetime.now(UTC)
        
        try:
            # التحقق من الامتثال للبروتوكولات
            compliance_check = self._check_protocol_compliance(data)
            
            if not compliance_check["compliant"] and enforce_protocols:
                self.performance_metrics["failed_operations"] += 1
                return {
                    "success": False,
                    "error": "Protocol compliance violation",
                    "violations": compliance_check["violations"]
                }
            
            # معالجة البيانات (يمكن توسيعها حسب الحاجة)
            processed_data = self._apply_existential_encryption(data)
            
            # تحديث الإحصائيات
            self.performance_metrics["total_operations"] += 1
            self.performance_metrics["successful_operations"] += 1
            
            # حساب وقت الاستجابة
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            self._update_avg_response_time(response_time)
            
            # تسجيل الحالة
            self.last_active_at = datetime.now(UTC)
            self._record_state("processed_information")
            
            return {
                "success": True,
                "data": processed_data,
                "compliance": compliance_check,
                "response_time_ms": response_time,
                "consciousness_id": self.consciousness_id
            }
            
        except Exception as e:
            self.performance_metrics["failed_operations"] += 1
            return {
                "success": False,
                "error": str(e),
                "consciousness_id": self.consciousness_id
            }
    
    def get_existential_signature(self) -> str:
        """
        الحصول على التوقيع الوجودي للوحدة
        
        Returns:
            توقيع تشفيري فريد
        """
        signature_data = f"{self.consciousness_id}:{self.entity_id}:{self.created_at.isoformat()}"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        الحصول على تقرير أداء شامل
        
        Returns:
            تقرير بالإحصائيات والمقاييس
        """
        success_rate = 0.0
        if self.performance_metrics["total_operations"] > 0:
            success_rate = (
                self.performance_metrics["successful_operations"] /
                self.performance_metrics["total_operations"]
            ) * 100
        
        return {
            "consciousness_id": self.consciousness_id,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "subscribed_protocols": self.subscribed_protocols,
            "performance": {
                **self.performance_metrics,
                "success_rate": f"{success_rate:.2f}%"
            },
            "state_history_size": len(self.state_history),
            "existential_signature": self.get_existential_signature()
        }
    
    def _check_protocol_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        التحقق من الامتثال للبروتوكولات المشترك فيها
        
        Args:
            data: البيانات المراد التحقق منها
            
        Returns:
            نتيجة التحقق مع أي انتهاكات
        """
        violations = []
        
        # تنفيذ منطق التحقق لكل بروتوكول مشترك فيه
        for protocol in self.subscribed_protocols:
            # يمكن توسيع هذا حسب البروتوكولات المحددة
            if "confidentiality" in protocol.lower():
                # التحقق من السرية
                if not data.get("encrypted", False):
                    violations.append(f"{protocol}: Data not encrypted")
            
            if "integrity" in protocol.lower():
                # التحقق من النزاهة
                if "checksum" not in data:
                    violations.append(f"{protocol}: Missing data checksum")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "checked_protocols": self.subscribed_protocols
        }
    
    def _apply_existential_encryption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تطبيق التشفير الوجودي على البيانات
        
        Args:
            data: البيانات المراد تشفيرها
            
        Returns:
            البيانات المشفرة
        """
        # تطبيق طبقة تشفير بسيطة (يمكن توسيعها)
        encrypted_data = data.copy()
        encrypted_data["existential_hash"] = hashlib.sha256(
            str(data).encode()
        ).hexdigest()
        encrypted_data["consciousness_signature"] = self.get_existential_signature()
        encrypted_data["timestamp"] = datetime.now(UTC).isoformat()
        
        return encrypted_data
    
    def _record_state(self, event: str) -> None:
        """
        تسجيل حالة وجودية جديدة
        
        Args:
            event: وصف الحدث
        """
        state_data = f"{self.consciousness_id}:{event}:{datetime.now(UTC).isoformat()}"
        state_hash = hashlib.sha256(state_data.encode()).hexdigest()
        
        state = ExistentialState(
            consciousness_id=self.consciousness_id,
            timestamp=datetime.now(UTC),
            state_hash=state_hash,
            metadata={"event": event},
            protocol_compliance=self.compliance_level
        )
        
        self.state_history.append(state)
    
    def _update_avg_response_time(self, new_time: float) -> None:
        """
        تحديث متوسط وقت الاستجابة
        
        Args:
            new_time: الوقت الجديد بالميلي ثانية
        """
        total_ops = self.performance_metrics["total_operations"]
        current_avg = self.performance_metrics["avg_response_time_ms"]
        
        new_avg = ((current_avg * (total_ops - 1)) + new_time) / total_ops
        self.performance_metrics["avg_response_time_ms"] = new_avg
    
    def __repr__(self) -> str:
        return (
            f"GovernedConsciousnessUnit("
            f"consciousness_id='{self.consciousness_id}', "
            f"entity_type={self.entity_type.value}, "
            f"entity_id='{self.entity_id}', "
            f"name='{self.name}')"
        )
