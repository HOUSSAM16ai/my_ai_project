# app/services/deployment_orchestrator_service.py
# ======================================================================================
# ==    SUPERHUMAN DEPLOYMENT ORCHESTRATOR - قابلية الاستبدال في الأنظمة العملاقة   ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام نشر خارق يتفوق على Google و Microsoft و AWS بسنوات ضوئية
#   ✨ المميزات الخارقة:
#   - Blue-Green Deployment (النشر الأزرق-الأخضر)
#   - Canary Releases (الإصدارات التدريجية)
#   - Rolling Updates (التحديثات المتدحرجة)
#   - Circuit Breaker Pattern (نمط قاطع الدائرة)
#   - Multi-level Health Checks (فحوصات صحة متعددة المستويات)
#   - Self-Healing (الشفاء الذاتي)
#   - Automated Rollback (التراجع التلقائي)
#   - Zero-Downtime Deployments (نشر بدون توقف)

from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable

from flask import current_app


# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class DeploymentStrategy(Enum):
    """استراتيجيات النشر"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    RECREATE = "recreate"
    A_B_TESTING = "ab_testing"
    SHADOW = "shadow"


class DeploymentPhase(Enum):
    """مراحل النشر"""
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    TESTING = "testing"
    TRAFFIC_SHIFTING = "traffic_shifting"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"


class HealthCheckType(Enum):
    """أنواع فحوصات الصحة"""
    LIVENESS = "liveness"      # هل الخدمة حية؟
    READINESS = "readiness"    # هل الخدمة جاهزة لاستقبال الطلبات؟
    STARTUP = "startup"        # هل اكتمل التشغيل؟


class CircuitState(Enum):
    """حالات قاطع الدائرة"""
    CLOSED = "closed"          # كل شيء يعمل
    OPEN = "open"              # فشل متكرر - إيقاف الطلبات
    HALF_OPEN = "half_open"    # محاولة تجريبية


class RollbackTrigger(Enum):
    """مُحفزات التراجع التلقائي"""
    ERROR_RATE_HIGH = "error_rate_high"
    LATENCY_HIGH = "latency_high"
    HEALTH_CHECK_FAILED = "health_check_failed"
    MANUAL = "manual"
    ANOMALY_DETECTED = "anomaly_detected"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class ServiceVersion:
    """نسخة الخدمة"""
    version_id: str
    service_name: str
    version_number: str
    image_tag: str
    replicas: int
    health_endpoint: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HealthCheck:
    """فحص الصحة"""
    check_id: str
    check_type: HealthCheckType
    endpoint: str
    initial_delay_seconds: int = 10
    period_seconds: int = 10
    timeout_seconds: int = 5
    success_threshold: int = 1
    failure_threshold: int = 3
    last_check: datetime | None = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    is_healthy: bool = False


@dataclass
class CircuitBreaker:
    """قاطع الدائرة - Circuit Breaker"""
    circuit_id: str
    service_name: str
    state: CircuitState = CircuitState.CLOSED
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_requests: int = 0
    total_failures: int = 0


@dataclass
class TrafficSplit:
    """توزيع الترافيك بين النسخ"""
    split_id: str
    deployment_id: str
    old_version_percentage: float = 100.0
    new_version_percentage: float = 0.0
    current_requests_old: int = 0
    current_requests_new: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DeploymentConfig:
    """تكوين النشر"""
    config_id: str
    strategy: DeploymentStrategy
    service_name: str
    old_version: ServiceVersion | None = None
    new_version: ServiceVersion
    canary_percentage_steps: list[float] = field(default_factory=lambda: [5, 10, 25, 50, 100])
    rollout_duration_minutes: int = 30
    health_checks: list[HealthCheck] = field(default_factory=list)
    auto_rollback_enabled: bool = True
    max_surge: int = 1  # عدد النسخ الإضافية أثناء التحديث
    max_unavailable: int = 0  # عدد النسخ التي يمكن أن تكون غير متاحة
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentStatus:
    """حالة النشر"""
    deployment_id: str
    config: DeploymentConfig
    phase: DeploymentPhase
    traffic_split: TrafficSplit | None = None
    circuit_breaker: CircuitBreaker
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    error_rate_old: float = 0.0
    error_rate_new: float = 0.0
    latency_p99_old: float = 0.0
    latency_p99_new: float = 0.0
    rollback_triggered: bool = False
    rollback_reason: RollbackTrigger | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricsSnapshot:
    """لقطة من المقاييس"""
    snapshot_id: str
    service_name: str
    version_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    error_rate: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0


# ======================================================================================
# DEPLOYMENT ORCHESTRATOR SERVICE
# ======================================================================================


class DeploymentOrchestrator:
    """
    نظام تنسيق النشر الخارق
    
    المميزات:
    - نشر بدون توقف (Zero-Downtime)
    - استبدال ذكي للخدمات
    - مراقبة مكثفة وتلقائية
    - تراجع فوري عند الفشل
    """

    def __init__(self):
        self._deployments: dict[str, DeploymentStatus] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._metrics: dict[str, deque[MetricsSnapshot]] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()
        self._monitoring_threads: dict[str, threading.Thread] = {}

    # ======================================================================================
    # BLUE-GREEN DEPLOYMENT
    # ======================================================================================

    def deploy_blue_green(
        self,
        service_name: str,
        new_version: ServiceVersion,
        old_version: ServiceVersion | None = None,
    ) -> str:
        """
        النشر الأزرق-الأخضر (Blue-Green Deployment)
        
        الآلية:
        1. البيئة الزرقاء (النسخة القديمة) ← العمل الحالي
        2. البيئة الخضراء (النسخة الجديدة) ← تشغيل وتجربة
        3. عند النجاح → تحويل الترافيك فورًا بنسبة 100%
        4. الاحتفاظ بالبيئة القديمة للتراجع السريع
        
        Args:
            service_name: اسم الخدمة
            new_version: النسخة الجديدة
            old_version: النسخة القديمة (اختياري)
            
        Returns:
            معرف النشر
        """
        deployment_id = str(uuid.uuid4())
        
        # إنشاء تكوين النشر
        config = DeploymentConfig(
            config_id=str(uuid.uuid4()),
            strategy=DeploymentStrategy.BLUE_GREEN,
            service_name=service_name,
            old_version=old_version,
            new_version=new_version,
            health_checks=[
                HealthCheck(
                    check_id=str(uuid.uuid4()),
                    check_type=HealthCheckType.STARTUP,
                    endpoint=new_version.health_endpoint,
                    initial_delay_seconds=15,
                ),
                HealthCheck(
                    check_id=str(uuid.uuid4()),
                    check_type=HealthCheckType.READINESS,
                    endpoint=new_version.health_endpoint,
                ),
                HealthCheck(
                    check_id=str(uuid.uuid4()),
                    check_type=HealthCheckType.LIVENESS,
                    endpoint=new_version.health_endpoint,
                ),
            ],
        )
        
        # إنشاء قاطع الدائرة
        circuit_breaker = CircuitBreaker(
            circuit_id=str(uuid.uuid4()),
            service_name=service_name,
        )
        
        # إنشاء حالة النشر
        status = DeploymentStatus(
            deployment_id=deployment_id,
            config=config,
            phase=DeploymentPhase.PREPARING,
            circuit_breaker=circuit_breaker,
        )
        
        with self._lock:
            self._deployments[deployment_id] = status
            self._circuit_breakers[service_name] = circuit_breaker
        
        # إضافة حدث
        self._add_event(deployment_id, "Blue-Green deployment initiated", {
            "service": service_name,
            "new_version": new_version.version_number,
        })
        
        # بدء عملية النشر في خيط منفصل
        thread = threading.Thread(
            target=self._execute_blue_green_deployment,
            args=(deployment_id,),
            daemon=True,
        )
        thread.start()
        self._monitoring_threads[deployment_id] = thread
        
        return deployment_id

    def _execute_blue_green_deployment(self, deployment_id: str):
        """تنفيذ النشر الأزرق-الأخضر"""
        status = self._deployments[deployment_id]
        
        try:
            # المرحلة 1: النشر
            self._update_phase(deployment_id, DeploymentPhase.DEPLOYING)
            self._add_event(deployment_id, "Deploying green environment")
            time.sleep(2)  # محاكاة النشر
            
            # المرحلة 2: الاختبار
            self._update_phase(deployment_id, DeploymentPhase.TESTING)
            self._add_event(deployment_id, "Running health checks on green environment")
            
            if not self._run_all_health_checks(deployment_id):
                raise Exception("Health checks failed on green environment")
            
            # المرحلة 3: تحويل الترافيك
            self._update_phase(deployment_id, DeploymentPhase.TRAFFIC_SHIFTING)
            self._add_event(deployment_id, "Switching traffic from blue to green (100%)")
            
            # تحويل فوري 100%
            traffic_split = TrafficSplit(
                split_id=str(uuid.uuid4()),
                deployment_id=deployment_id,
                old_version_percentage=0.0,
                new_version_percentage=100.0,
            )
            
            with self._lock:
                status.traffic_split = traffic_split
            
            time.sleep(1)
            
            # المرحلة 4: المراقبة
            self._update_phase(deployment_id, DeploymentPhase.MONITORING)
            self._add_event(deployment_id, "Monitoring new version")
            
            if not self._monitor_deployment(deployment_id, duration_seconds=60):
                raise Exception("Monitoring detected issues - triggering rollback")
            
            # النجاح
            self._update_phase(deployment_id, DeploymentPhase.COMPLETED)
            self._add_event(deployment_id, "Blue-Green deployment completed successfully")
            
            with self._lock:
                status.completed_at = datetime.now(UTC)
            
        except Exception as e:
            self._handle_deployment_failure(deployment_id, str(e))

    # ======================================================================================
    # CANARY DEPLOYMENT
    # ======================================================================================

    def deploy_canary(
        self,
        service_name: str,
        new_version: ServiceVersion,
        old_version: ServiceVersion,
        canary_steps: list[float] | None = None,
    ) -> str:
        """
        الإصدار التدريجي (Canary Release)
        
        الآلية:
        1. نشر الإصدار الجديد لنسبة صغيرة من المستخدمين (5-10%)
        2. مراقبة مكثفة للأداء والأخطاء
        3. زيادة تدريجية: 5% → 10% → 25% → 50% → 100%
        4. التراجع الفوري عند اكتشاف مشاكل
        
        Args:
            service_name: اسم الخدمة
            new_version: النسخة الجديدة
            old_version: النسخة القديمة
            canary_steps: خطوات النسب المئوية (اختياري)
            
        Returns:
            معرف النشر
        """
        deployment_id = str(uuid.uuid4())
        
        if canary_steps is None:
            canary_steps = [5, 10, 25, 50, 100]
        
        config = DeploymentConfig(
            config_id=str(uuid.uuid4()),
            strategy=DeploymentStrategy.CANARY,
            service_name=service_name,
            old_version=old_version,
            new_version=new_version,
            canary_percentage_steps=canary_steps,
            health_checks=[
                HealthCheck(
                    check_id=str(uuid.uuid4()),
                    check_type=HealthCheckType.READINESS,
                    endpoint=new_version.health_endpoint,
                    period_seconds=5,
                ),
            ],
        )
        
        circuit_breaker = CircuitBreaker(
            circuit_id=str(uuid.uuid4()),
            service_name=service_name,
            failure_threshold=3,  # أكثر حساسية للفشل
        )
        
        traffic_split = TrafficSplit(
            split_id=str(uuid.uuid4()),
            deployment_id=deployment_id,
            old_version_percentage=100.0,
            new_version_percentage=0.0,
        )
        
        status = DeploymentStatus(
            deployment_id=deployment_id,
            config=config,
            phase=DeploymentPhase.PREPARING,
            traffic_split=traffic_split,
            circuit_breaker=circuit_breaker,
        )
        
        with self._lock:
            self._deployments[deployment_id] = status
            self._circuit_breakers[service_name] = circuit_breaker
        
        self._add_event(deployment_id, "Canary deployment initiated", {
            "service": service_name,
            "steps": canary_steps,
        })
        
        thread = threading.Thread(
            target=self._execute_canary_deployment,
            args=(deployment_id,),
            daemon=True,
        )
        thread.start()
        self._monitoring_threads[deployment_id] = thread
        
        return deployment_id

    def _execute_canary_deployment(self, deployment_id: str):
        """تنفيذ النشر التدريجي"""
        status = self._deployments[deployment_id]
        config = status.config
        
        try:
            # المرحلة 1: النشر الأولي
            self._update_phase(deployment_id, DeploymentPhase.DEPLOYING)
            self._add_event(deployment_id, "Deploying canary version")
            time.sleep(2)
            
            # المرحلة 2: التحويل التدريجي
            self._update_phase(deployment_id, DeploymentPhase.TRAFFIC_SHIFTING)
            
            for step_percentage in config.canary_percentage_steps:
                self._add_event(
                    deployment_id,
                    f"Shifting traffic to canary: {step_percentage}%",
                )
                
                # تحديث توزيع الترافيك
                with self._lock:
                    if status.traffic_split:
                        status.traffic_split.new_version_percentage = step_percentage
                        status.traffic_split.old_version_percentage = 100.0 - step_percentage
                        status.traffic_split.last_updated = datetime.now(UTC)
                
                # المراقبة المكثفة عند كل خطوة
                self._update_phase(deployment_id, DeploymentPhase.MONITORING)
                
                # مدة المراقبة تزداد مع زيادة النسبة
                monitoring_duration = int(30 * (step_percentage / 100))
                monitoring_duration = max(monitoring_duration, 15)  # على الأقل 15 ثانية
                
                if not self._monitor_deployment(deployment_id, duration_seconds=monitoring_duration):
                    raise Exception(f"Issues detected at {step_percentage}% traffic")
                
                self._add_event(
                    deployment_id,
                    f"Step {step_percentage}% completed successfully",
                )
                
                # الانتقال للخطوة التالية
                if step_percentage < 100:
                    self._update_phase(deployment_id, DeploymentPhase.TRAFFIC_SHIFTING)
                    time.sleep(2)
            
            # النجاح
            self._update_phase(deployment_id, DeploymentPhase.COMPLETED)
            self._add_event(deployment_id, "Canary deployment completed successfully")
            
            with self._lock:
                status.completed_at = datetime.now(UTC)
            
        except Exception as e:
            self._handle_deployment_failure(deployment_id, str(e))

    # ======================================================================================
    # ROLLING UPDATE
    # ======================================================================================

    def deploy_rolling(
        self,
        service_name: str,
        new_version: ServiceVersion,
        old_version: ServiceVersion,
        max_surge: int = 1,
        max_unavailable: int = 0,
    ) -> str:
        """
        التحديث المتدحرج (Rolling Update)
        
        الآلية:
        1. استبدال تدريجي للمكونات واحدًا تلو الآخر
        2. الحفاظ على عدد كافٍ من النسخ العاملة دائمًا
        3. max_surge: عدد النسخ الإضافية المسموحة أثناء التحديث
        4. max_unavailable: عدد النسخ التي يمكن أن تكون غير متاحة
        
        Args:
            service_name: اسم الخدمة
            new_version: النسخة الجديدة
            old_version: النسخة القديمة
            max_surge: النسخ الإضافية المسموحة
            max_unavailable: النسخ غير المتاحة المسموحة
            
        Returns:
            معرف النشر
        """
        deployment_id = str(uuid.uuid4())
        
        config = DeploymentConfig(
            config_id=str(uuid.uuid4()),
            strategy=DeploymentStrategy.ROLLING,
            service_name=service_name,
            old_version=old_version,
            new_version=new_version,
            max_surge=max_surge,
            max_unavailable=max_unavailable,
            health_checks=[
                HealthCheck(
                    check_id=str(uuid.uuid4()),
                    check_type=HealthCheckType.READINESS,
                    endpoint=new_version.health_endpoint,
                ),
            ],
        )
        
        circuit_breaker = CircuitBreaker(
            circuit_id=str(uuid.uuid4()),
            service_name=service_name,
        )
        
        status = DeploymentStatus(
            deployment_id=deployment_id,
            config=config,
            phase=DeploymentPhase.PREPARING,
            circuit_breaker=circuit_breaker,
        )
        
        with self._lock:
            self._deployments[deployment_id] = status
            self._circuit_breakers[service_name] = circuit_breaker
        
        self._add_event(deployment_id, "Rolling update initiated", {
            "service": service_name,
            "max_surge": max_surge,
            "max_unavailable": max_unavailable,
        })
        
        thread = threading.Thread(
            target=self._execute_rolling_deployment,
            args=(deployment_id,),
            daemon=True,
        )
        thread.start()
        self._monitoring_threads[deployment_id] = thread
        
        return deployment_id

    def _execute_rolling_deployment(self, deployment_id: str):
        """تنفيذ التحديث المتدحرج"""
        status = self._deployments[deployment_id]
        config = status.config
        
        try:
            self._update_phase(deployment_id, DeploymentPhase.DEPLOYING)
            
            total_replicas = config.new_version.replicas
            
            # استبدال النسخ واحدة تلو الأخرى
            for i in range(total_replicas):
                self._add_event(
                    deployment_id,
                    f"Updating replica {i + 1}/{total_replicas}",
                )
                
                # نشر النسخة الجديدة
                time.sleep(1)
                
                # فحص الصحة
                if not self._run_all_health_checks(deployment_id):
                    raise Exception(f"Health check failed for replica {i + 1}")
                
                # إيقاف النسخة القديمة المقابلة
                if i < total_replicas:
                    self._add_event(
                        deployment_id,
                        f"Terminating old replica {i + 1}",
                    )
                    time.sleep(0.5)
            
            # المراقبة النهائية
            self._update_phase(deployment_id, DeploymentPhase.MONITORING)
            if not self._monitor_deployment(deployment_id, duration_seconds=30):
                raise Exception("Post-deployment monitoring failed")
            
            # النجاح
            self._update_phase(deployment_id, DeploymentPhase.COMPLETED)
            self._add_event(deployment_id, "Rolling update completed successfully")
            
            with self._lock:
                status.completed_at = datetime.now(UTC)
            
        except Exception as e:
            self._handle_deployment_failure(deployment_id, str(e))

    # ======================================================================================
    # CIRCUIT BREAKER PATTERN
    # ======================================================================================

    def execute_with_circuit_breaker(
        self,
        service_name: str,
        func: Callable,
        fallback: Callable | None = None,
    ) -> Any:
        """
        تنفيذ مع قاطع الدائرة (Circuit Breaker Pattern)
        
        الآلية:
        - CLOSED: كل شيء يعمل - السماح بالطلبات
        - OPEN: فشل متكرر - إيقاف الطلبات والتحويل للبديل
        - HALF_OPEN: محاولة تجريبية بعد مهلة زمنية
        
        Args:
            service_name: اسم الخدمة
            func: الدالة المراد تنفيذها
            fallback: دالة بديلة عند الفشل
            
        Returns:
            نتيجة التنفيذ أو البديل
        """
        # إنشاء قاطع دائرة إذا لم يكن موجودًا
        if service_name not in self._circuit_breakers:
            with self._lock:
                self._circuit_breakers[service_name] = CircuitBreaker(
                    circuit_id=str(uuid.uuid4()),
                    service_name=service_name,
                )
        
        circuit = self._circuit_breakers[service_name]
        
        with self._lock:
            circuit.total_requests += 1
            
            # التحقق من حالة الدائرة
            if circuit.state == CircuitState.OPEN:
                # التحقق من انتهاء المهلة الزمنية
                if circuit.last_failure_time:
                    elapsed = (datetime.now(UTC) - circuit.last_failure_time).total_seconds()
                    if elapsed >= circuit.timeout_seconds:
                        # الانتقال لحالة HALF_OPEN
                        circuit.state = CircuitState.HALF_OPEN
                        circuit.last_state_change = datetime.now(UTC)
                    else:
                        # الدائرة ما زالت مفتوحة - استخدام البديل
                        if fallback:
                            return fallback()
                        raise Exception(f"Circuit breaker is OPEN for {service_name}")
        
        # محاولة التنفيذ
        try:
            result = func()
            
            with self._lock:
                circuit.failure_count = 0
                circuit.success_count += 1
                
                # إذا كانت الدائرة HALF_OPEN وتم النجاح
                if circuit.state == CircuitState.HALF_OPEN:
                    if circuit.success_count >= circuit.success_threshold:
                        # إغلاق الدائرة
                        circuit.state = CircuitState.CLOSED
                        circuit.last_state_change = datetime.now(UTC)
                        circuit.success_count = 0
            
            return result
            
        except Exception as e:
            with self._lock:
                circuit.failure_count += 1
                circuit.total_failures += 1
                circuit.last_failure_time = datetime.now(UTC)
                circuit.success_count = 0
                
                # فتح الدائرة عند تجاوز العتبة
                if circuit.failure_count >= circuit.failure_threshold:
                    circuit.state = CircuitState.OPEN
                    circuit.last_state_change = datetime.now(UTC)
            
            # استخدام البديل
            if fallback:
                return fallback()
            
            raise

    # ======================================================================================
    # HEALTH CHECKS
    # ======================================================================================

    def _run_all_health_checks(self, deployment_id: str) -> bool:
        """
        تشغيل جميع فحوصات الصحة
        
        Returns:
            True إذا نجحت جميع الفحوصات
        """
        status = self._deployments[deployment_id]
        
        for health_check in status.config.health_checks:
            if not self._run_health_check(health_check):
                self._add_event(
                    deployment_id,
                    f"{health_check.check_type.value} health check failed",
                    {"endpoint": health_check.endpoint},
                )
                return False
        
        return True

    def _run_health_check(self, health_check: HealthCheck) -> bool:
        """
        تشغيل فحص صحة واحد
        
        في الإنتاج، يتم إجراء طلب HTTP فعلي للنقطة النهائية
        هنا نحاكي الفحص
        """
        # محاكاة الفحص (في الإنتاج: HTTP request)
        import random
        success = random.random() > 0.1  # 90% نسبة نجاح
        
        health_check.last_check = datetime.now(UTC)
        
        if success:
            health_check.consecutive_successes += 1
            health_check.consecutive_failures = 0
            
            if health_check.consecutive_successes >= health_check.success_threshold:
                health_check.is_healthy = True
        else:
            health_check.consecutive_failures += 1
            health_check.consecutive_successes = 0
            
            if health_check.consecutive_failures >= health_check.failure_threshold:
                health_check.is_healthy = False
        
        return health_check.is_healthy

    # ======================================================================================
    # MONITORING & ROLLBACK
    # ======================================================================================

    def _monitor_deployment(self, deployment_id: str, duration_seconds: int) -> bool:
        """
        مراقبة النشر واكتشاف الشذوذات
        
        Returns:
            True إذا كانت المراقبة ناجحة
        """
        status = self._deployments[deployment_id]
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds:
            # محاكاة جمع المقاييس
            metrics = self._collect_metrics(deployment_id)
            
            # التحقق من معدل الأخطاء
            if metrics.error_rate > 5.0:  # 5% error rate threshold
                self._trigger_rollback(
                    deployment_id,
                    RollbackTrigger.ERROR_RATE_HIGH,
                    f"Error rate: {metrics.error_rate}%",
                )
                return False
            
            # التحقق من زمن الاستجابة
            if metrics.latency_p99 > 5000:  # 5 seconds threshold
                self._trigger_rollback(
                    deployment_id,
                    RollbackTrigger.LATENCY_HIGH,
                    f"P99 latency: {metrics.latency_p99}ms",
                )
                return False
            
            # فحص الصحة
            if not self._run_all_health_checks(deployment_id):
                self._trigger_rollback(
                    deployment_id,
                    RollbackTrigger.HEALTH_CHECK_FAILED,
                    "Health checks failed during monitoring",
                )
                return False
            
            time.sleep(5)
        
        return True

    def _collect_metrics(self, deployment_id: str) -> MetricsSnapshot:
        """
        جمع المقاييس للنسخة الجديدة
        
        في الإنتاج، يتم جمع المقاييس من Prometheus أو نظام مراقبة آخر
        """
        import random
        
        status = self._deployments[deployment_id]
        
        # محاكاة المقاييس
        total = random.randint(100, 1000)
        failed = int(total * random.uniform(0, 0.03))  # 0-3% error rate
        
        metrics = MetricsSnapshot(
            snapshot_id=str(uuid.uuid4()),
            service_name=status.config.service_name,
            version_id=status.config.new_version.version_id,
            total_requests=total,
            successful_requests=total - failed,
            failed_requests=failed,
            error_rate=(failed / total * 100) if total > 0 else 0,
            latency_p50=random.uniform(50, 200),
            latency_p95=random.uniform(200, 800),
            latency_p99=random.uniform(500, 2000),
            cpu_usage=random.uniform(20, 70),
            memory_usage=random.uniform(30, 80),
        )
        
        # حفظ المقاييس
        service_version_key = f"{status.config.service_name}:{status.config.new_version.version_id}"
        self._metrics[service_version_key].append(metrics)
        
        return metrics

    def _trigger_rollback(
        self,
        deployment_id: str,
        trigger: RollbackTrigger,
        reason: str,
    ):
        """
        تفعيل التراجع التلقائي (Automated Rollback)
        """
        status = self._deployments[deployment_id]
        
        with self._lock:
            status.rollback_triggered = True
            status.rollback_reason = trigger
        
        self._add_event(
            deployment_id,
            f"ROLLBACK TRIGGERED: {trigger.value}",
            {"reason": reason},
        )
        
        self._update_phase(deployment_id, DeploymentPhase.ROLLING_BACK)
        
        # تراجع فوري
        if status.config.old_version:
            self._add_event(deployment_id, "Rolling back to previous version")
            
            # إعادة الترافيك للنسخة القديمة
            if status.traffic_split:
                with self._lock:
                    status.traffic_split.old_version_percentage = 100.0
                    status.traffic_split.new_version_percentage = 0.0
                    status.traffic_split.last_updated = datetime.now(UTC)
            
            time.sleep(2)
            
            self._add_event(deployment_id, "Rollback completed")
        
        self._update_phase(deployment_id, DeploymentPhase.FAILED)

    def _handle_deployment_failure(self, deployment_id: str, error_message: str):
        """معالجة فشل النشر"""
        self._add_event(
            deployment_id,
            "Deployment failed",
            {"error": error_message},
        )
        
        # التراجع التلقائي إذا كان مفعلاً
        status = self._deployments[deployment_id]
        if status.config.auto_rollback_enabled and not status.rollback_triggered:
            self._trigger_rollback(
                deployment_id,
                RollbackTrigger.MANUAL,
                error_message,
            )
        else:
            self._update_phase(deployment_id, DeploymentPhase.FAILED)

    # ======================================================================================
    # UTILITY METHODS
    # ======================================================================================

    def _update_phase(self, deployment_id: str, phase: DeploymentPhase):
        """تحديث مرحلة النشر"""
        with self._lock:
            if deployment_id in self._deployments:
                self._deployments[deployment_id].phase = phase

    def _add_event(
        self,
        deployment_id: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ):
        """إضافة حدث لسجل النشر"""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
            "metadata": metadata or {},
        }
        
        with self._lock:
            if deployment_id in self._deployments:
                self._deployments[deployment_id].events.append(event)

    def get_deployment_status(self, deployment_id: str) -> DeploymentStatus | None:
        """الحصول على حالة النشر"""
        return self._deployments.get(deployment_id)

    def get_circuit_breaker_status(self, service_name: str) -> CircuitBreaker | None:
        """الحصول على حالة قاطع الدائرة"""
        return self._circuit_breakers.get(service_name)

    def get_metrics(self, service_name: str, version_id: str, limit: int = 100) -> list[MetricsSnapshot]:
        """الحصول على المقاييس"""
        key = f"{service_name}:{version_id}"
        metrics_list = list(self._metrics.get(key, []))
        return metrics_list[-limit:]


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_orchestrator_instance: DeploymentOrchestrator | None = None
_orchestrator_lock = threading.Lock()


def get_deployment_orchestrator() -> DeploymentOrchestrator:
    """الحصول على نسخة واحدة من منسق النشر (Singleton)"""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        with _orchestrator_lock:
            if _orchestrator_instance is None:
                _orchestrator_instance = DeploymentOrchestrator()
    
    return _orchestrator_instance
