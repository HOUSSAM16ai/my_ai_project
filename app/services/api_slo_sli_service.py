# app/services/api_slo_sli_service.py
# ======================================================================================
# ==        SUPERHUMAN SLO/SLI TRACKING SERVICE (v1.0 - RELIABILITY EDITION)       ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام تتبع SLO/SLI خارق يتفوق على Google SRE
#   ✨ المميزات الخارقة:
#   - Service Level Objectives (SLO) management
#   - Service Level Indicators (SLI) real-time tracking
#   - Error budget calculation and alerting
#   - Multi-window SLO evaluation (30d, 7d, 24h)
#   - Burn rate analysis and forecasting
#   - SLO compliance reporting
#   - Incident impact tracking

import statistics
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class SLIType(Enum):
    """Service Level Indicator types"""

    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    QUALITY = "quality"


class SLOStatus(Enum):
    """SLO compliance status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    BREACHED = "breached"


class BurnRateLevel(Enum):
    """Error budget burn rate levels"""

    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class SLI:
    """Service Level Indicator"""

    name: str
    sli_type: SLIType
    description: str
    measurement_window: int  # seconds
    target_value: float
    current_value: float = 0.0
    measurements: deque = field(default_factory=lambda: deque(maxlen=10000))
    last_updated: datetime | None = None


@dataclass
class SLO:
    """Service Level Objective"""

    slo_id: str
    name: str
    description: str
    sli_name: str
    target: float  # e.g., 99.9 for 99.9%
    window_days: int  # e.g., 30 for 30-day rolling window
    error_budget: float = field(init=False)  # Calculated from target
    error_budget_remaining: float = 0.0
    status: SLOStatus = SLOStatus.HEALTHY
    alert_threshold: float = 0.1  # Alert when 10% of error budget consumed

    def __post_init__(self):
        # Error budget is (100 - target)%
        self.error_budget = 100.0 - self.target


@dataclass
class SLOMeasurement:
    """SLO measurement record"""

    timestamp: datetime
    slo_id: str
    actual_value: float
    target_value: float
    compliance: bool
    error_budget_consumed: float


@dataclass
class ErrorBudgetBurn:
    """Error budget burn rate analysis"""

    slo_id: str
    timestamp: datetime
    burn_rate_1h: float  # Hourly burn rate
    burn_rate_6h: float  # 6-hour burn rate
    burn_rate_24h: float  # Daily burn rate
    burn_rate_7d: float  # Weekly burn rate
    level: BurnRateLevel
    projected_depletion: datetime | None = None


@dataclass
class IncidentImpact:
    """Incident impact on SLOs"""

    incident_id: str
    started_at: datetime
    ended_at: datetime | None
    affected_slos: list[str]
    error_budget_consumed: dict[str, float]
    severity: str


# ======================================================================================
# SLI TRACKING SERVICE
# ======================================================================================


class SLITracker:
    """
    Service Level Indicator tracker

    Tracks real-time metrics for SLI calculation
    """

    def __init__(self):
        self.slis: dict[str, SLI] = {}
        self.lock = threading.RLock()

    def register_sli(self, sli: SLI):
        """Register a new SLI"""
        with self.lock:
            self.slis[sli.name] = sli

    def record_measurement(self, sli_name: str, value: float, timestamp: datetime | None = None):
        """Record a measurement for an SLI"""
        if timestamp is None:
            timestamp = datetime.now(UTC)

        with self.lock:
            if sli_name not in self.slis:
                return False

            sli = self.slis[sli_name]
            sli.measurements.append((timestamp, value))
            sli.last_updated = timestamp

            # Calculate current value (moving average)
            if sli.measurements:
                recent_values = [v for _, v in list(sli.measurements)[-100:]]
                sli.current_value = statistics.mean(recent_values)

            return True

    def get_sli_value(self, sli_name: str, window_seconds: int | None = None) -> float | None:
        """Get SLI value for a time window"""
        with self.lock:
            if sli_name not in self.slis:
                return None

            sli = self.slis[sli_name]

            if not window_seconds:
                return sli.current_value

            # Calculate value for specific window
            cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
            recent_measurements = [v for t, v in sli.measurements if t >= cutoff]

            if not recent_measurements:
                return None

            if sli.sli_type == SLIType.AVAILABILITY:
                # Availability: percentage of successful requests
                return statistics.mean(recent_measurements)
            elif sli.sli_type == SLIType.LATENCY:
                # Latency: p99 or similar percentile
                # Need at least 2 data points for quantiles
                if len(recent_measurements) < 2:
                    return recent_measurements[0] if recent_measurements else None
                return statistics.quantiles(recent_measurements, n=100)[98]  # P99
            elif sli.sli_type == SLIType.ERROR_RATE:
                # Error rate: percentage of failed requests
                return statistics.mean(recent_measurements)
            else:
                return statistics.mean(recent_measurements)

    def get_all_slis(self) -> dict[str, dict[str, Any]]:
        """Get all SLIs with current values"""
        with self.lock:
            return {
                name: {
                    "type": sli.sli_type.value,
                    "description": sli.description,
                    "current_value": sli.current_value,
                    "target_value": sli.target_value,
                    "last_updated": sli.last_updated.isoformat() if sli.last_updated else None,
                    "measurement_count": len(sli.measurements),
                }
                for name, sli in self.slis.items()
            }


# ======================================================================================
# SLO MANAGEMENT SERVICE
# ======================================================================================


class SLOService:
    """
    خدمة إدارة SLO الخارقة - Superhuman SLO Management Service

    Features:
    - Multi-window SLO tracking (30d, 7d, 24h, 1h)
    - Error budget calculation and monitoring
    - Burn rate analysis with forecasting
    - SLO compliance alerting
    - Incident impact tracking
    - Automated reporting
    """

    def __init__(self):
        self.slos: dict[str, SLO] = {}
        self.sli_tracker = SLITracker()
        self.measurements: deque = deque(maxlen=100000)
        self.burn_rate_history: deque = deque(maxlen=10000)
        self.incidents: dict[str, IncidentImpact] = {}
        self.lock = threading.RLock()

        # Initialize default SLOs
        self._initialize_default_slos()

    def _initialize_default_slos(self):
        """Initialize default SLOs for the API"""

        # Availability SLI and SLO
        availability_sli = SLI(
            name="api_availability",
            sli_type=SLIType.AVAILABILITY,
            description="Percentage of successful API requests",
            measurement_window=60,
            target_value=99.9,
        )
        self.sli_tracker.register_sli(availability_sli)

        self.slos["availability_30d"] = SLO(
            slo_id="slo_avail_30d",
            name="API Availability (30d)",
            description="99.9% of requests succeed over 30 days",
            sli_name="api_availability",
            target=99.9,
            window_days=30,
        )

        # Latency SLI and SLO
        latency_sli = SLI(
            name="api_latency_p99",
            sli_type=SLIType.LATENCY,
            description="99th percentile API response time",
            measurement_window=60,
            target_value=500.0,  # 500ms
        )
        self.sli_tracker.register_sli(latency_sli)

        self.slos["latency_30d"] = SLO(
            slo_id="slo_lat_30d",
            name="API Latency P99 (30d)",
            description="99% of requests complete within 500ms over 30 days",
            sli_name="api_latency_p99",
            target=99.0,
            window_days=30,
        )

        # Error Rate SLI and SLO
        error_rate_sli = SLI(
            name="api_error_rate",
            sli_type=SLIType.ERROR_RATE,
            description="Percentage of API requests resulting in errors",
            measurement_window=60,
            target_value=0.1,  # 0.1% error rate
        )
        self.sli_tracker.register_sli(error_rate_sli)

        self.slos["error_rate_30d"] = SLO(
            slo_id="slo_err_30d",
            name="API Error Rate (30d)",
            description="Less than 0.1% error rate over 30 days",
            sli_name="api_error_rate",
            target=99.9,  # 99.9% success = 0.1% error
            window_days=30,
        )

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        timestamp: datetime | None = None,
    ):
        """Record an API request for SLI/SLO tracking"""
        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Track availability
        is_success = 200 <= status_code < 500  # 5xx are failures
        self.sli_tracker.record_measurement(
            "api_availability", 100.0 if is_success else 0.0, timestamp
        )

        # Track latency
        is_fast = response_time_ms <= 500.0
        self.sli_tracker.record_measurement("api_latency_p99", 100.0 if is_fast else 0.0, timestamp)

        # Track error rate
        is_error = status_code >= 400
        self.sli_tracker.record_measurement(
            "api_error_rate", 0.0 if not is_error else 100.0, timestamp
        )

        # Update SLO measurements
        self._update_slo_measurements()

    def _update_slo_measurements(self):
        """Update SLO compliance measurements"""
        with self.lock:
            for slo_id, slo in self.slos.items():
                # Get SLI value for the SLO window
                window_seconds = slo.window_days * 24 * 3600
                actual_value = self.sli_tracker.get_sli_value(slo.sli_name, window_seconds)

                if actual_value is None:
                    continue

                # Check compliance
                is_compliant = actual_value >= slo.target

                # Calculate error budget consumption
                if is_compliant:
                    error_consumed = 0.0
                else:
                    error_consumed = ((slo.target - actual_value) / slo.error_budget) * 100.0

                # Update SLO
                slo.error_budget_remaining = max(0.0, 100.0 - error_consumed)

                # Determine status
                if slo.error_budget_remaining <= 0:
                    slo.status = SLOStatus.BREACHED
                elif slo.error_budget_remaining <= 10:
                    slo.status = SLOStatus.CRITICAL
                elif slo.error_budget_remaining <= 25:
                    slo.status = SLOStatus.WARNING
                else:
                    slo.status = SLOStatus.HEALTHY

                # Record measurement
                measurement = SLOMeasurement(
                    timestamp=datetime.now(UTC),
                    slo_id=slo_id,
                    actual_value=actual_value,
                    target_value=slo.target,
                    compliance=is_compliant,
                    error_budget_consumed=error_consumed,
                )
                self.measurements.append(measurement)

    def calculate_burn_rate(self, slo_id: str) -> ErrorBudgetBurn:
        """Calculate error budget burn rate"""
        with self.lock:
            if slo_id not in self.slos:
                return None

            slo = self.slos[slo_id]
            now = datetime.now(UTC)

            # Get measurements for different windows
            measurements_1h = [
                m
                for m in self.measurements
                if m.slo_id == slo_id and m.timestamp >= now - timedelta(hours=1)
            ]
            measurements_6h = [
                m
                for m in self.measurements
                if m.slo_id == slo_id and m.timestamp >= now - timedelta(hours=6)
            ]
            measurements_24h = [
                m
                for m in self.measurements
                if m.slo_id == slo_id and m.timestamp >= now - timedelta(hours=24)
            ]
            measurements_7d = [
                m
                for m in self.measurements
                if m.slo_id == slo_id and m.timestamp >= now - timedelta(days=7)
            ]

            # Calculate burn rates (% of error budget consumed per hour)
            def calc_burn(measurements, hours):
                if not measurements:
                    return 0.0
                consumed = sum(m.error_budget_consumed for m in measurements)
                return consumed / hours if hours > 0 else 0.0

            burn_1h = calc_burn(measurements_1h, 1)
            burn_6h = calc_burn(measurements_6h, 6)
            burn_24h = calc_burn(measurements_24h, 24)
            burn_7d = calc_burn(measurements_7d, 7 * 24)

            # Determine burn rate level
            if burn_1h > 10.0:  # Consuming 10% per hour = depleted in 10 hours
                level = BurnRateLevel.CRITICAL
            elif burn_1h > 5.0:
                level = BurnRateLevel.HIGH
            elif burn_1h > 2.0:
                level = BurnRateLevel.ELEVATED
            else:
                level = BurnRateLevel.NORMAL

            # Project depletion time
            projected_depletion = None
            if burn_1h > 0:
                hours_remaining = slo.error_budget_remaining / burn_1h
                projected_depletion = now + timedelta(hours=hours_remaining)

            burn = ErrorBudgetBurn(
                slo_id=slo_id,
                timestamp=now,
                burn_rate_1h=burn_1h,
                burn_rate_6h=burn_6h,
                burn_rate_24h=burn_24h,
                burn_rate_7d=burn_7d,
                level=level,
                projected_depletion=projected_depletion,
            )

            self.burn_rate_history.append(burn)

            return burn

    def start_incident(self, incident_id: str, affected_slos: list[str], severity: str) -> bool:
        """Start tracking an incident"""
        with self.lock:
            if incident_id in self.incidents:
                return False

            self.incidents[incident_id] = IncidentImpact(
                incident_id=incident_id,
                started_at=datetime.now(UTC),
                ended_at=None,
                affected_slos=affected_slos,
                error_budget_consumed={},
                severity=severity,
            )

            return True

    def end_incident(self, incident_id: str) -> bool:
        """End an incident and calculate impact"""
        with self.lock:
            if incident_id not in self.incidents:
                return False

            incident = self.incidents[incident_id]
            incident.ended_at = datetime.now(UTC)

            # Calculate error budget consumed during incident
            for slo_id in incident.affected_slos:
                measurements = [
                    m
                    for m in self.measurements
                    if m.slo_id == slo_id
                    and incident.started_at <= m.timestamp <= incident.ended_at
                ]
                consumed = sum(m.error_budget_consumed for m in measurements)
                incident.error_budget_consumed[slo_id] = consumed

            return True

    def get_slo_status(self, slo_id: str) -> dict[str, Any] | None:
        """Get detailed SLO status"""
        with self.lock:
            if slo_id not in self.slos:
                return None

            slo = self.slos[slo_id]
            burn_rate = self.calculate_burn_rate(slo_id)

            return {
                "slo_id": slo.slo_id,
                "name": slo.name,
                "description": slo.description,
                "target": slo.target,
                "window_days": slo.window_days,
                "error_budget_total": slo.error_budget,
                "error_budget_remaining": slo.error_budget_remaining,
                "status": slo.status.value,
                "burn_rate": (
                    {
                        "level": burn_rate.level.value,
                        "1h": burn_rate.burn_rate_1h,
                        "6h": burn_rate.burn_rate_6h,
                        "24h": burn_rate.burn_rate_24h,
                        "7d": burn_rate.burn_rate_7d,
                        "projected_depletion": (
                            burn_rate.projected_depletion.isoformat()
                            if burn_rate.projected_depletion
                            else None
                        ),
                    }
                    if burn_rate
                    else None
                ),
            }

    def get_dashboard(self) -> dict[str, Any]:
        """Get SLO/SLI dashboard data"""
        with self.lock:
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "slis": self.sli_tracker.get_all_slis(),
                "slos": {slo_id: self.get_slo_status(slo_id) for slo_id in self.slos.keys()},
                "active_incidents": len([i for i in self.incidents.values() if i.ended_at is None]),
                "overall_health": self._calculate_overall_health(),
            }

    def _calculate_overall_health(self) -> str:
        """Calculate overall system health based on SLOs"""
        if not self.slos:
            return "unknown"

        statuses = [slo.status for slo in self.slos.values()]

        if any(s == SLOStatus.BREACHED for s in statuses) or any(s == SLOStatus.CRITICAL for s in statuses):
            return "critical"
        elif any(s == SLOStatus.WARNING for s in statuses):
            return "warning"
        else:
            return "healthy"


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_slo_service_instance: SLOService | None = None
_slo_lock = threading.Lock()


def get_slo_service() -> SLOService:
    """Get singleton SLO service instance"""
    global _slo_service_instance

    if _slo_service_instance is None:
        with _slo_lock:
            if _slo_service_instance is None:
                _slo_service_instance = SLOService()

    return _slo_service_instance
