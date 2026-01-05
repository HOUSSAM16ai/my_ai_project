from __future__ import annotations

from app.services.observability.aiops.service import AIOpsService, get_aiops_service
from app.telemetry.unified_observability import (
    UnifiedObservabilityService,
    get_unified_observability,
)

class ObservabilityBoundaryService:
    """
    خدمة مراقبة حدية موحدة.
    تجمع إشارات AIOps والقياسات والتتبع في واجهة نظيفة واحدة،
    وتطبق مبدأ فصل المسؤوليات بعزل الموجه عن تفاصيل التنفيذ الداخلية.
    """

    def __init__(
        self,
        aiops_service: AIOpsService | None = None,
        telemetry_service: UnifiedObservabilityService | None = None,
    ):
        self.aiops = aiops_service or get_aiops_service()
        self.telemetry = telemetry_service or get_unified_observability()

    async def get_system_health(self) -> dict[str, object]:
        """
        تجميع الحالة الصحية للنظام من مصادر متعددة بطريقة خفيفة الوزن.
        """
        return {
            "status": "ok",
            "system": "superhuman",
            "timestamp": self.telemetry.get_golden_signals()["timestamp"],
        }

    async def get_golden_signals(self) -> dict[str, object]:
        """
        استرجاع الإشارات الذهبية الخاصة بالموثوقية (زمن الاستجابة، الحركة، الأخطاء، التشبع).
        """
        return self.telemetry.get_golden_signals()

    async def get_aiops_metrics(self) -> dict[str, object]:
        """
        استرجاع مقاييس AIOps للشذوذات وقرارات المعالجة الذاتية.
        """
        return self.aiops.get_aiops_metrics()

    async def get_performance_snapshot(self) -> dict[str, object]:
        """
        الحصول على لقطة شاملة لإحصاءات الأداء.
        """
        return self.telemetry.get_statistics()

    async def get_endpoint_analytics(self, path: str) -> list[dict[str, object]]:
        """
        تحليل آثار التتبع لمسار واجهة برمجة تطبيقات محدد.
        """
        return self.telemetry.find_traces_by_criteria(operation_name=path)

    async def get_active_alerts(self) -> list[object]:
        """
        استرجاع التنبيهات النشطة المتعلقة بالشذوذات من النظام.
        """
        # Convert deque to list
        return list(self.telemetry.anomaly_alerts)
