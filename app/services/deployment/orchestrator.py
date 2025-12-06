# app/services/deployment/orchestrator.py
"""
Core Orchestrator Logic (Refactored).
"""

from __future__ import annotations

import logging
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .types import (
    CircuitBreakerStatus,
    CircuitState,
    DeploymentConfig,
    DeploymentPhase,
    DeploymentStatus,
    DeploymentStrategy,
    HealthCheckConfig,
    HealthCheckType,
    ServiceVersion,
    TrafficSplit,
)

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("deployment_orchestrator")


class DeploymentOrchestrator:
    """
    منسق النشر المركزي (Central Deployment Orchestrator)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._deployments: dict[str, DeploymentStatus] = {}
        self._circuit_breakers: dict[str, CircuitBreakerStatus] = {}
        self._metrics_buffer: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._active_rollouts: dict[str, str] = {}  # service_name -> deployment_id
        self._initialized = True
        _LOG.info("Deployment Orchestrator Initialized (Hyper-Scale Mode)")

    # ==================================================================================
    # Public API - Deployment Requests
    # ==================================================================================

    def deploy_blue_green(
        self,
        service_name: str,
        new_version: ServiceVersion,
        old_version: ServiceVersion | None = None,
        auto_rollback: bool = True,
    ) -> str:
        """بدء نشر أزرق-أخضر"""
        config = DeploymentConfig(
            strategy=DeploymentStrategy.BLUE_GREEN,
            service_name=service_name,
            new_version=new_version,
            old_version=old_version,
            auto_rollback=auto_rollback,
            health_checks=self._get_default_health_checks(new_version.health_endpoint),
        )
        return self._start_deployment(config)

    def deploy_canary(
        self,
        service_name: str,
        new_version: ServiceVersion,
        old_version: ServiceVersion,
        canary_steps: list[int] | None = None,
        interval_seconds: int = 60,
    ) -> str:
        """بدء نشر تدريجي (Canary)"""
        config = DeploymentConfig(
            strategy=DeploymentStrategy.CANARY,
            service_name=service_name,
            new_version=new_version,
            old_version=old_version,
            canary_percentage_steps=canary_steps or [10, 50, 100],
            canary_interval_seconds=interval_seconds,
            health_checks=self._get_default_health_checks(new_version.health_endpoint),
            traffic_shifting_enabled=True,
        )

        # Initial traffic split state (0% new)
        deployment_id = self._start_deployment(config)
        status = self.get_deployment_status(deployment_id)
        if status:
            status.traffic_split = TrafficSplit(
                new_version_percentage=0, old_version_percentage=100
            )

        return deployment_id

    def deploy_rolling(
        self,
        service_name: str,
        new_version: ServiceVersion,
        old_version: ServiceVersion,
        max_surge: int = 1,
        max_unavailable: int = 0,
    ) -> str:
        """بدء تحديث متدحرج (Rolling Update)"""
        config = DeploymentConfig(
            strategy=DeploymentStrategy.ROLLING,
            service_name=service_name,
            new_version=new_version,
            old_version=old_version,
            max_surge=max_surge,
            max_unavailable=max_unavailable,
            health_checks=self._get_default_health_checks(new_version.health_endpoint),
        )
        return self._start_deployment(config)

    def get_deployment_status(self, deployment_id: str) -> DeploymentStatus | None:
        """الحصول على حالة النشر"""
        return self._deployments.get(deployment_id)

    def get_metrics(self, service_name: str, version_id: str) -> list[dict]:
        """الحصول على مقاييس النشر"""
        key = f"{service_name}:{version_id}"
        return list(self._metrics_buffer[key])

    # ==================================================================================
    # Circuit Breaker Logic
    # ==================================================================================

    def execute_with_circuit_breaker(
        self,
        service_name: str,
        operation: Callable,
        fallback: Callable | None = None,
        *args,
        **kwargs,
    ) -> Any:
        """تنفيذ عملية محمية بقاطع الدائرة"""
        breaker = self._get_or_create_circuit_breaker(service_name)

        if breaker.state == CircuitState.OPEN:
            # التحقق مما إذا كان يجب محاولة الإغلاق (Half-Open)
            if (
                breaker.last_failure_time
                and (datetime.now(UTC) - breaker.last_failure_time).total_seconds()
                > breaker.reset_timeout_seconds
            ):
                breaker.state = CircuitState.HALF_OPEN
                _LOG.warning(f"Circuit Breaker for {service_name} enters HALF_OPEN state")
            else:
                if fallback:
                    return fallback()
                raise Exception(f"Circuit Breaker is OPEN for {service_name}")

        try:
            result = operation(*args, **kwargs)
            self._record_circuit_success(breaker)
            return result
        except Exception as e:
            self._record_circuit_failure(breaker)
            if fallback:
                return fallback()
            raise e

    def get_circuit_breaker_status(self, service_name: str) -> CircuitBreakerStatus:
        """الحصول على حالة قاطع الدائرة"""
        return self._get_or_create_circuit_breaker(service_name)

    def _get_or_create_circuit_breaker(self, service_name: str) -> CircuitBreakerStatus:
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = CircuitBreakerStatus(
                service_name=service_name, state=CircuitState.CLOSED
            )
        return self._circuit_breakers[service_name]

    def _record_circuit_success(self, breaker: CircuitBreakerStatus):
        breaker.last_success_time = datetime.now(UTC)
        breaker.consecutive_failures = 0
        if breaker.state == CircuitState.HALF_OPEN:
            breaker.state = CircuitState.CLOSED
            _LOG.info(f"Circuit Breaker for {breaker.service_name} CLOSED (Recovered)")

    def _record_circuit_failure(self, breaker: CircuitBreakerStatus):
        breaker.last_failure_time = datetime.now(UTC)
        breaker.total_failures += 1
        breaker.consecutive_failures += 1

        if breaker.state == CircuitState.CLOSED and breaker.consecutive_failures >= 5:
            breaker.state = CircuitState.OPEN
            _LOG.error(f"Circuit Breaker for {breaker.service_name} OPENED due to failures")

        elif breaker.state == CircuitState.HALF_OPEN:
            breaker.state = CircuitState.OPEN
            _LOG.error(
                f"Circuit Breaker for {breaker.service_name} Re-OPENED (Failed in Half-Open)"
            )

    # ==================================================================================
    # Internal Orchestration Logic
    # ==================================================================================

    def _start_deployment(self, config: DeploymentConfig) -> str:
        deployment_id = str(uuid.uuid4())
        status = DeploymentStatus(
            deployment_id=deployment_id, config=config, phase=DeploymentPhase.PREPARING
        )
        self._deployments[deployment_id] = status
        self._active_rollouts[config.service_name] = deployment_id

        # بدء عملية النشر في خيط منفصل (Background Thread)
        # في نظام حقيقي، سيكون هذا عبر Celery أو Task Queue
        threading.Thread(
            target=self._execute_deployment_workflow, args=(deployment_id,), daemon=True
        ).start()

        return deployment_id

    def _execute_deployment_workflow(self, deployment_id: str):
        """تنفيذ تدفق النشر"""
        status = self._deployments.get(deployment_id)
        if not status:
            return

        try:
            self._log_event(status, "Deployment workflow initiated")

            # 1. Provision Resources
            self._update_phase(status, DeploymentPhase.DEPLOYING)
            self._simulate_provisioning(status)

            # 2. Health Checks
            self._update_phase(status, DeploymentPhase.TESTING)
            if not self._run_health_checks(status):
                self._handle_failure(status, "Initial health checks failed")
                return

            # 3. Traffic Shifting
            self._update_phase(status, DeploymentPhase.TRAFFIC_SHIFTING)
            self._execute_traffic_shifting(status)

            # 4. Completion
            if status.phase != DeploymentPhase.ROLLING_BACK:
                self._update_phase(status, DeploymentPhase.COMPLETED)
                self._log_event(status, "Deployment completed successfully")

        except Exception as e:
            _LOG.exception(f"Deployment failed: {e}")
            self._handle_failure(status, str(e))

    def _execute_traffic_shifting(self, status: DeploymentStatus):
        """تنفيذ منطق تحويل الترافيك بناءً على الاستراتيجية"""
        config = status.config

        if config.strategy == DeploymentStrategy.BLUE_GREEN:
            # تحويل كامل بعد التحقق
            self._wait_and_monitor(status, 2)
            status.traffic_split = TrafficSplit(
                new_version_percentage=100, old_version_percentage=0
            )
            self._log_event(status, "Traffic switched 100% to Blue/Green new version")

        elif config.strategy == DeploymentStrategy.CANARY:
            # تحويل تدريجي
            current_pct = 0
            for step in config.canary_percentage_steps:
                if status.phase == DeploymentPhase.FAILED:
                    break

                # التحقق من الصحة قبل كل خطوة
                if not self._run_health_checks(status):
                    self._handle_failure(status, f"Health check failed at {current_pct}%")
                    return

                current_pct = step
                status.traffic_split = TrafficSplit(
                    new_version_percentage=current_pct,
                    old_version_percentage=100 - current_pct,
                )
                self._log_event(status, f"Canary traffic increased to {current_pct}%")

                # انتظار فترة المراقبة
                # استخدام وقت قصير للاختبارات
                sleep_time = (
                    1 if getattr(self, "_testing_mode", False) else config.canary_interval_seconds
                )
                self._wait_and_monitor(status, sleep_time)

        elif config.strategy == DeploymentStrategy.ROLLING:
            # تحديث متدحرج
            self._log_event(status, "Rolling update started")
            total_replicas = config.new_version.replicas
            for i in range(total_replicas):
                self._wait_and_monitor(status, 1)  # محاكاة استبدال Pod
                self._log_event(status, f"Updated replica {i + 1}/{total_replicas}")

    def _wait_and_monitor(self, status: DeploymentStatus, duration: float):
        """الانتظار مع مراقبة ومحاكاة المقاييس"""
        start_time = time.time()
        while time.time() - start_time < duration:
            # Simulate metric collection
            self._collect_metrics(status)
            time.sleep(min(0.5, duration))

    def _collect_metrics(self, status: DeploymentStatus):
        """جمع مقاييس محاكاة"""
        key = f"{status.config.service_name}:{status.config.new_version.version_id}"
        metric = {
            "timestamp": datetime.now(UTC).isoformat(),
            "cpu_usage": random.uniform(10, 80),
            "memory_usage": random.uniform(200, 1024),
            "requests_per_second": random.randint(50, 500),
            "error_rate": random.uniform(0, 0.05),
        }
        self._metrics_buffer[key].append(metric)

    def _run_health_checks(self, status: DeploymentStatus) -> bool:
        """تشغيل فحوصات الصحة"""
        # محاكاة فحوصات الصحة
        # استخدام random هنا لتجنب إزالة الاستيراد
        _ = random.random()

        # في بيئة الاختبار، نريد نتائج حتمية غالباً، لكن هنا نحاكي الواقع
        # للتبسيط، ننجح دائمًا إلا إذا تم حقن خطأ (لم يتم تنفيذه هنا)
        return True

    def _handle_failure(self, status: DeploymentStatus, reason: str):
        """معالجة الفشل والتراجع"""
        _LOG.error(f"Deployment {status.deployment_id} failed: {reason}")
        status.errors.append(reason)

        if status.config.auto_rollback:
            self._update_phase(status, DeploymentPhase.ROLLING_BACK)
            self._log_event(status, "Auto-rollback initiated")
            time.sleep(2)  # محاكاة التراجع
            self._update_phase(status, DeploymentPhase.FAILED)  # النهاية هي فشل النشر الأصلي
            self._log_event(status, "Rollback completed")
        else:
            self._update_phase(status, DeploymentPhase.FAILED)

    def _simulate_provisioning(self, status: DeploymentStatus):
        """محاكاة توفير الموارد"""
        time.sleep(1)
        self._log_event(status, f"Provisioned resources for {status.config.new_version.version_id}")

    def _update_phase(self, status: DeploymentStatus, phase: DeploymentPhase):
        status.phase = phase
        self._log_event(status, f"Phase changed to {phase.value}")

    def _log_event(self, status: DeploymentStatus, message: str):
        event = {
            "timestamp": datetime.now(UTC),
            "message": message,
            "phase": status.phase.value,
        }
        status.events.append(event)
        _LOG.info(f"[{status.deployment_id}] {message}")

    def _get_default_health_checks(self, endpoint: str) -> list[HealthCheckConfig]:
        return [
            HealthCheckConfig(HealthCheckType.STARTUP, endpoint),
            HealthCheckConfig(HealthCheckType.READINESS, endpoint),
            HealthCheckConfig(HealthCheckType.LIVENESS, endpoint),
        ]


def get_deployment_orchestrator() -> DeploymentOrchestrator:
    return DeploymentOrchestrator()
