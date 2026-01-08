"""
مدير التنبيهات (Alert Manager).

يدير التنبيهات والإشعارات بناءً على المقاييس والأحداث.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """مستوى خطورة التنبيه."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """حالة التنبيه."""
    
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass(slots=True)
class Alert:
    """
    تنبيه واحد.
    
    Attributes:
        alert_id: معرف فريد
        name: اسم التنبيه
        severity: مستوى الخطورة
        message: رسالة التنبيه
        status: حالة التنبيه
        created_at: وقت الإنشاء
        resolved_at: وقت الحل
        metadata: بيانات إضافية
    """
    
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AlertRule:
    """
    قاعدة تنبيه.
    
    Attributes:
        name: اسم القاعدة
        condition: شرط التنبيه
        severity: مستوى الخطورة
        message_template: قالب الرسالة
        cooldown_seconds: فترة الانتظار بين التنبيهات
    """
    
    name: str
    condition: Callable[[], bool | Coroutine[Any, Any, bool]]
    severity: AlertSeverity
    message_template: str
    cooldown_seconds: int = 300  # 5 دقائق


type AlertHandler = Callable[[Alert], Coroutine[Any, Any, None]]


class AlertManager:
    """
    مدير التنبيهات المتقدم.
    
    يدير التنبيهات مع دعم:
    - قواعد مخصصة
    - معالجات متعددة
    - فترة انتظار (cooldown)
    - تجميع التنبيهات
    - إشعارات متعددة القنوات
    
    المبادئ:
    - Rule-Based: قواعد مرنة وقابلة للتخصيص
    - Multi-Channel: دعم قنوات إشعار متعددة
    - Smart Grouping: تجميع ذكي للتنبيهات
    - Cooldown: منع الإزعاج بالتنبيهات المتكررة
    """
    
    def __init__(self) -> None:
        """تهيئة مدير التنبيهات."""
        self._rules: dict[str, AlertRule] = {}
        self._alerts: dict[str, Alert] = {}
        self._handlers: list[AlertHandler] = []
        self._last_alert_time: dict[str, datetime] = {}
        self._running = False
        self._check_task: asyncio.Task[None] | None = None
        
        logger.info("✅ Alert Manager initialized")
    
    def add_rule(self, rule: AlertRule) -> None:
        """
        يضيف قاعدة تنبيه.
        
        Args:
            rule: قاعدة التنبيه
        """
        self._rules[rule.name] = rule
        logger.info(f"✅ Alert rule added: {rule.name}")
    
    def remove_rule(self, name: str) -> bool:
        """
        يزيل قاعدة تنبيه.
        
        Args:
            name: اسم القاعدة
            
        Returns:
            bool: True إذا تم الإزالة
        """
        if name in self._rules:
            del self._rules[name]
            logger.info(f"✅ Alert rule removed: {name}")
            return True
        return False
    
    def add_handler(self, handler: AlertHandler) -> None:
        """
        يضيف معالج تنبيهات.
        
        Args:
            handler: معالج التنبيهات
        """
        self._handlers.append(handler)
        logger.info(f"✅ Alert handler added: {handler.__name__}")
    
    async def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> Alert:
        """
        يطلق تنبيهاً يدوياً.
        
        Args:
            name: اسم التنبيه
            severity: مستوى الخطورة
            message: رسالة التنبيه
            metadata: بيانات إضافية
            
        Returns:
            Alert: التنبيه المُنشأ
        """
        # التحقق من cooldown
        if not self._check_cooldown(name):
            logger.debug(f"⏳ Alert '{name}' is in cooldown period")
            # إرجاع التنبيه الموجود
            return self._alerts[name]
        
        # إنشاء التنبيه
        alert = Alert(
            alert_id=f"{name}_{datetime.utcnow().timestamp()}",
            name=name,
            severity=severity,
            message=message,
            metadata=metadata or {},
        )
        
        # حفظ التنبيه
        self._alerts[alert.alert_id] = alert
        self._last_alert_time[name] = datetime.utcnow()
        
        # إرسال إلى المعالجات
        await self._notify_handlers(alert)
        
        logger.warning(f"🚨 Alert triggered: {name} ({severity.value})")
        
        return alert
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """
        يحل تنبيهاً.
        
        Args:
            alert_id: معرف التنبيه
            
        Returns:
            bool: True إذا تم الحل
        """
        if alert_id not in self._alerts:
            return False
        
        alert = self._alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        logger.info(f"✅ Alert resolved: {alert.name}")
        
        return True
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """
        يقر بتنبيه.
        
        Args:
            alert_id: معرف التنبيه
            
        Returns:
            bool: True إذا تم الإقرار
        """
        if alert_id not in self._alerts:
            return False
        
        alert = self._alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        
        logger.info(f"✅ Alert acknowledged: {alert.name}")
        
        return True
    
    async def silence_alert(self, name: str, duration_seconds: int) -> bool:
        """
        يكتم تنبيهاً لفترة محددة.
        
        Args:
            name: اسم التنبيه
            duration_seconds: مدة الكتم بالثواني
            
        Returns:
            bool: True إذا تم الكتم
        """
        # تحديث وقت آخر تنبيه لمنع التنبيهات الجديدة
        self._last_alert_time[name] = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        logger.info(f"🔇 Alert silenced: {name} for {duration_seconds}s")
        
        return True
    
    def get_active_alerts(self) -> list[Alert]:
        """
        يحصل على التنبيهات النشطة.
        
        Returns:
            list[Alert]: قائمة التنبيهات النشطة
        """
        return [
            alert for alert in self._alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> list[Alert]:
        """
        يحصل على التنبيهات حسب مستوى الخطورة.
        
        Args:
            severity: مستوى الخطورة
            
        Returns:
            list[Alert]: قائمة التنبيهات
        """
        return [
            alert for alert in self._alerts.values()
            if alert.severity == severity
        ]
    
    def get_alert_stats(self) -> dict[str, Any]:
        """
        يحصل على إحصائيات التنبيهات.
        
        Returns:
            dict[str, Any]: إحصائيات مفصلة
        """
        alerts = list(self._alerts.values())
        
        return {
            "total_alerts": len(alerts),
            "active_alerts": len([a for a in alerts if a.status == AlertStatus.ACTIVE]),
            "resolved_alerts": len([a for a in alerts if a.status == AlertStatus.RESOLVED]),
            "by_severity": {
                "info": len([a for a in alerts if a.severity == AlertSeverity.INFO]),
                "warning": len([a for a in alerts if a.severity == AlertSeverity.WARNING]),
                "error": len([a for a in alerts if a.severity == AlertSeverity.ERROR]),
                "critical": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            },
            "rules_count": len(self._rules),
            "handlers_count": len(self._handlers),
        }
    
    async def start_monitoring(self, check_interval: int = 60) -> None:
        """
        يبدأ مراقبة القواعد.
        
        Args:
            check_interval: فترة الفحص بالثواني
        """
        if self._running:
            logger.warning("⚠️ Alert monitoring already running")
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._monitoring_loop(check_interval))
        logger.info("✅ Alert monitoring started")
    
    async def stop_monitoring(self) -> None:
        """يوقف مراقبة القواعد."""
        self._running = False
        
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Alert monitoring stopped")
    
    async def _monitoring_loop(self, check_interval: int) -> None:
        """
        حلقة المراقبة الدورية.
        
        Args:
            check_interval: فترة الفحص بالثواني
        """
        while self._running:
            try:
                await self._check_all_rules()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"❌ Error in monitoring loop: {exc}", exc_info=True)
                await asyncio.sleep(check_interval)
    
    async def _check_all_rules(self) -> None:
        """يفحص جميع القواعد."""
        for rule in self._rules.values():
            try:
                # تقييم الشرط
                condition_result = rule.condition()
                
                # إذا كان الشرط coroutine، انتظره
                if asyncio.iscoroutine(condition_result):
                    condition_result = await condition_result
                
                # إطلاق تنبيه إذا تحقق الشرط
                if condition_result:
                    await self.trigger_alert(
                        name=rule.name,
                        severity=rule.severity,
                        message=rule.message_template,
                    )
            
            except Exception as exc:
                logger.error(
                    f"❌ Error checking rule '{rule.name}': {exc}",
                    exc_info=True,
                )
    
    def _check_cooldown(self, name: str) -> bool:
        """
        يتحقق من فترة الانتظار.
        
        Args:
            name: اسم التنبيه
            
        Returns:
            bool: True إذا انتهت فترة الانتظار
        """
        if name not in self._last_alert_time:
            return True
        
        rule = self._rules.get(name)
        if not rule:
            return True
        
        time_since_last = datetime.utcnow() - self._last_alert_time[name]
        return time_since_last.total_seconds() >= rule.cooldown_seconds
    
    async def _notify_handlers(self, alert: Alert) -> None:
        """
        يشعر المعالجات بالتنبيه.
        
        Args:
            alert: التنبيه
        """
        for handler in self._handlers:
            try:
                await handler(alert)
            except Exception as exc:
                logger.error(
                    f"❌ Error in alert handler {handler.__name__}: {exc}",
                    exc_info=True,
                )


# مثيل عام
_global_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """
    يحصل على مدير التنبيهات العام.
    
    Returns:
        AlertManager: مدير التنبيهات
    """
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager
