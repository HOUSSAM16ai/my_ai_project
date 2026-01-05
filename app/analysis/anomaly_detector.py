"""كاشف شذوذ مبسّط مصمم لتوفير تنبيهات واضحة للمبتدئين."""

from dataclasses import dataclass
from enum import Enum


class SeverityLevel(str, Enum):
    """درجات خطورة للحالات الشاذة تسهّل تصنيف التنبيهات."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """تمثيل شفاف للحالة الشاذة بدرجة وشرح."""

    score: float
    severity: SeverityLevel
    description: str


class AnomalyDetector:
    """كاشف شذوذ بسيط يعتمد عتبات واضحة لسهولة التفسير."""

    def __init__(self, high_threshold_ms: float = 750.0, critical_threshold_ms: float = 1500.0):
        self.high_threshold_ms = high_threshold_ms
        self.critical_threshold_ms = critical_threshold_ms

    def check_value(self, metric: str, value_ms: float) -> tuple[bool, Anomaly | None]:
        """يقيّم القيمة ويعيد حالة شاذة اختيارية بناءً على العتبات."""

        if value_ms < 0:
            return False, None

        if value_ms >= self.critical_threshold_ms:
            anomaly = Anomaly(
                score=value_ms / self.critical_threshold_ms,
                severity=SeverityLevel.CRITICAL,
                description=f"القيمة {metric} تجاوزت الحد الحرج",
            )
            return True, anomaly

        if value_ms >= self.high_threshold_ms:
            anomaly = Anomaly(
                score=value_ms / self.high_threshold_ms,
                severity=SeverityLevel.HIGH,
                description=f"القيمة {metric} فوق الحد المرتفع",
            )
            return True, anomaly

        return False, None
