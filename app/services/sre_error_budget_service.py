# app/services/sre_error_budget_service.py
# ======================================================================================
# ==          SUPERHUMAN SRE & ERROR BUDGET SERVICE (v1.0 - ULTIMATE)             ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام SRE و Error Budget خارق يتفوق على Google SRE
#   ✨ المميزات الخارقة:
#   - SLO/SLI tracking and management
#   - Error budget calculation and monitoring
#   - Canary and blue-green deployments
#   - Release risk assessment
#   - Chaos engineering integration

from __future__ import annotations

import threading
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from flask import current_app

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class DeploymentStrategy(Enum):
    """Deployment strategies"""

    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    RECREATE = "recreate"


class ErrorBudgetStatus(Enum):
    """Error budget status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    EXHAUSTED = "exhausted"
    CRITICAL = "critical"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class SLO:
    """Service Level Objective"""

    slo_id: str
    service_name: str
    name: str
    description: str
    target_percentage: float  # e.g., 99.9
    measurement_window_days: int
    sli_type: str  # availability, latency, error_rate
    threshold_value: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SLI:
    """Service Level Indicator measurement"""

    sli_id: str
    slo_id: str
    measured_value: float
    target_value: float
    compliant: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ErrorBudget:
    """Error budget tracking"""

    budget_id: str
    slo_id: str
    service_name: str
    budget_percentage: float  # Remaining error budget
    consumed_percentage: float
    total_requests: int
    failed_requests: int
    status: ErrorBudgetStatus
    window_start: datetime
    window_end: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DeploymentRisk:
    """Deployment risk assessment"""

    risk_id: str
    deployment_id: str
    service_name: str
    strategy: DeploymentStrategy
    risk_score: float  # 0-1, higher is riskier
    error_budget_impact: float
    recommendation: str
    factors: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CanaryDeployment:
    """Canary deployment configuration"""

    deployment_id: str
    service_name: str
    canary_percentage: float
    duration_minutes: int
    success_criteria: dict[str, float]
    started_at: datetime
    current_status: str = "running"
    metrics: dict[str, float] = field(default_factory=dict)


# ======================================================================================
# SRE & ERROR BUDGET SERVICE
# ======================================================================================


class SREErrorBudgetService:
    """
    خدمة SRE و Error Budget الخارقة - World-class SRE practices

    Features:
    - SLO/SLI management
    - Error budget tracking
    - Deployment risk assessment
    - Canary deployments
    - Release gating based on error budget
    """

    def __init__(self):
        self.slos: dict[str, SLO] = {}
        self.sli_measurements: dict[str, deque[SLI]] = defaultdict(lambda: deque(maxlen=10000))
        self.error_budgets: dict[str, ErrorBudget] = {}
        self.deployment_risks: dict[str, DeploymentRisk] = {}
        self.canary_deployments: dict[str, CanaryDeployment] = {}
        self.lock = threading.RLock()  # Use RLock to prevent deadlock with nested calls

        current_app.logger.info("SRE & Error Budget Service initialized")

    # ==================================================================================
    # SLO/SLI MANAGEMENT
    # ==================================================================================

    def create_slo(self, slo: SLO) -> bool:
        """Create Service Level Objective"""
        with self.lock:
            self.slos[slo.slo_id] = slo

            # Initialize error budget
            self._calculate_error_budget(slo.slo_id)

            current_app.logger.info(f"Created SLO: {slo.name} ({slo.target_percentage}%)")
            return True

    def record_sli(self, sli: SLI):
        """Record SLI measurement"""
        with self.lock:
            self.sli_measurements[sli.slo_id].append(sli)

            # Update error budget
            self._update_error_budget(sli.slo_id)

    def _calculate_error_budget(self, slo_id: str):
        """Calculate error budget for SLO"""
        slo = self.slos.get(slo_id)
        if not slo:
            return

        # Error budget = 100 - target percentage
        budget_percentage = 100.0 - slo.target_percentage

        window_start = datetime.now(UTC) - timedelta(days=slo.measurement_window_days)
        window_end = datetime.now(UTC)

        error_budget = ErrorBudget(
            budget_id=str(uuid.uuid4()),
            slo_id=slo_id,
            service_name=slo.service_name,
            budget_percentage=budget_percentage,
            consumed_percentage=0.0,
            total_requests=0,
            failed_requests=0,
            status=ErrorBudgetStatus.HEALTHY,
            window_start=window_start,
            window_end=window_end,
        )

        with self.lock:
            self.error_budgets[slo_id] = error_budget

    def _update_error_budget(self, slo_id: str):
        """Update error budget based on SLI measurements"""
        budget = self.error_budgets.get(slo_id)
        slo = self.slos.get(slo_id)

        if not budget or not slo:
            return

        # Get measurements in window
        measurements = list(self.sli_measurements.get(slo_id, []))
        window_measurements = [m for m in measurements if m.timestamp >= budget.window_start]

        if not window_measurements:
            return

        # Calculate compliance
        total = len(window_measurements)
        compliant = len([m for m in window_measurements if m.compliant])

        actual_percentage = (compliant / total) * 100 if total > 0 else 100
        consumed = 100 - actual_percentage

        # Update budget
        budget.total_requests = total
        budget.failed_requests = total - compliant
        budget.consumed_percentage = consumed

        # Determine status
        if consumed >= budget.budget_percentage:
            budget.status = ErrorBudgetStatus.EXHAUSTED
        elif consumed >= budget.budget_percentage * 0.8:
            budget.status = ErrorBudgetStatus.CRITICAL
        elif consumed >= budget.budget_percentage * 0.5:
            budget.status = ErrorBudgetStatus.WARNING
        else:
            budget.status = ErrorBudgetStatus.HEALTHY

    # ==================================================================================
    # DEPLOYMENT RISK ASSESSMENT
    # ==================================================================================

    def assess_deployment_risk(
        self, deployment_id: str, service_name: str, strategy: DeploymentStrategy
    ) -> DeploymentRisk:
        """Assess deployment risk based on error budget"""
        # Get service SLOs
        service_slos = [s for s in self.slos.values() if s.service_name == service_name]

        risk_score = 0.0
        error_budget_impact = 0.0
        factors = {}

        # Check error budgets
        for slo in service_slos:
            budget = self.error_budgets.get(slo.slo_id)
            if budget:
                if budget.status == ErrorBudgetStatus.EXHAUSTED:
                    risk_score += 0.9
                    factors[f"error_budget_{slo.name}"] = "exhausted"
                elif budget.status == ErrorBudgetStatus.CRITICAL:
                    risk_score += 0.7
                    factors[f"error_budget_{slo.name}"] = "critical"
                elif budget.status == ErrorBudgetStatus.WARNING:
                    risk_score += 0.4
                    factors[f"error_budget_{slo.name}"] = "warning"

                error_budget_impact += budget.consumed_percentage

        # Normalize risk score
        risk_score = min(risk_score / len(service_slos), 1.0) if service_slos else 0.5

        # Adjust for strategy
        if strategy == DeploymentStrategy.CANARY:
            risk_score *= 0.3  # Canary reduces risk
        elif strategy == DeploymentStrategy.BLUE_GREEN:
            risk_score *= 0.5
        elif strategy == DeploymentStrategy.RECREATE:
            risk_score *= 1.5  # Recreate is riskier

        # Generate recommendation
        if risk_score > 0.7:
            recommendation = (
                "BLOCK: Error budget exhausted. Delay deployment until budget recovers."
            )
        elif risk_score > 0.5:
            recommendation = "CAUTION: Use canary deployment with increased monitoring."
        else:
            recommendation = "PROCEED: Error budget healthy. Safe to deploy."

        risk = DeploymentRisk(
            risk_id=str(uuid.uuid4()),
            deployment_id=deployment_id,
            service_name=service_name,
            strategy=strategy,
            risk_score=risk_score,
            error_budget_impact=error_budget_impact,
            recommendation=recommendation,
            factors=factors,
        )

        with self.lock:
            self.deployment_risks[deployment_id] = risk

        current_app.logger.info(
            f"Deployment risk assessed: {service_name} - Risk: {risk_score:.2f}"
        )

        return risk

    # ==================================================================================
    # CANARY DEPLOYMENTS
    # ==================================================================================

    def start_canary_deployment(
        self,
        service_name: str,
        canary_percentage: float,
        duration_minutes: int,
        success_criteria: dict[str, float],
    ) -> CanaryDeployment:
        """Start canary deployment"""
        deployment = CanaryDeployment(
            deployment_id=str(uuid.uuid4()),
            service_name=service_name,
            canary_percentage=canary_percentage,
            duration_minutes=duration_minutes,
            success_criteria=success_criteria,
            started_at=datetime.now(UTC),
        )

        with self.lock:
            self.canary_deployments[deployment.deployment_id] = deployment

        current_app.logger.info(f"Started canary deployment: {service_name} ({canary_percentage}%)")

        return deployment

    def update_canary_metrics(
        self, deployment_id: str, metrics: dict[str, float]
    ) -> dict[str, Any]:
        """Update canary metrics and check success criteria"""
        deployment = self.canary_deployments.get(deployment_id)
        if not deployment:
            return {"success": False, "reason": "Deployment not found"}

        deployment.metrics = metrics

        # Check success criteria
        all_passed = True
        failures = []

        for metric, threshold in deployment.success_criteria.items():
            actual_value = metrics.get(metric)
            if actual_value is None or actual_value > threshold:
                all_passed = False
                failures.append(f"{metric}: {actual_value} > {threshold}")

        if all_passed:
            deployment.current_status = "success"
            return {"success": True, "action": "promote"}
        else:
            deployment.current_status = "failed"
            return {"success": False, "action": "rollback", "failures": failures}

    # ==================================================================================
    # METRICS
    # ==================================================================================

    def get_sre_metrics(self) -> dict[str, Any]:
        """Get SRE metrics"""
        return {
            "total_slos": len(self.slos),
            "error_budgets": {
                "healthy": len(
                    [
                        b
                        for b in self.error_budgets.values()
                        if b.status == ErrorBudgetStatus.HEALTHY
                    ]
                ),
                "warning": len(
                    [
                        b
                        for b in self.error_budgets.values()
                        if b.status == ErrorBudgetStatus.WARNING
                    ]
                ),
                "critical": len(
                    [
                        b
                        for b in self.error_budgets.values()
                        if b.status == ErrorBudgetStatus.CRITICAL
                    ]
                ),
                "exhausted": len(
                    [
                        b
                        for b in self.error_budgets.values()
                        if b.status == ErrorBudgetStatus.EXHAUSTED
                    ]
                ),
            },
            "deployment_risks": len(self.deployment_risks),
            "high_risk_deployments": len(
                [d for d in self.deployment_risks.values() if d.risk_score > 0.7]
            ),
            "active_canaries": len(
                [c for c in self.canary_deployments.values() if c.current_status == "running"]
            ),
        }

    def get_service_sre_status(self, service_name: str) -> dict[str, Any]:
        """Get SRE status for service"""
        service_slos = [s for s in self.slos.values() if s.service_name == service_name]

        budgets = []
        for slo in service_slos:
            budget = self.error_budgets.get(slo.slo_id)
            if budget:
                budgets.append(
                    {
                        "slo_name": slo.name,
                        "target": slo.target_percentage,
                        "budget_remaining": budget.budget_percentage - budget.consumed_percentage,
                        "status": budget.status.value,
                    }
                )

        return {
            "service_name": service_name,
            "total_slos": len(service_slos),
            "error_budgets": budgets,
            "deployment_allowed": all(b["status"] != "exhausted" for b in budgets),
        }


# ======================================================================================
# SINGLETON
# ======================================================================================

_sre_instance: SREErrorBudgetService | None = None
_sre_lock = threading.Lock()


def get_sre_service() -> SREErrorBudgetService:
    """Get singleton SRE service instance"""
    global _sre_instance

    if _sre_instance is None:
        with _sre_lock:
            if _sre_instance is None:
                _sre_instance = SREErrorBudgetService()

    return _sre_instance
