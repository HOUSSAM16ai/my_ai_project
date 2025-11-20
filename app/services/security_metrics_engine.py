"""
🚀 Security Metrics & Analytics Engine
Based on: Google's Security Command Center, Meta's Security Platform
Features: ML-based risk scoring, predictive analytics, anomaly detection
"""

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

# ============================================================
# 📊 DATA MODELS
# ============================================================


@dataclass
class SecurityFinding:
    """نموذج واحد من نتائج الفحص الأمني"""

    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    rule_id: str
    file_path: str
    line_number: int
    message: str
    cwe_id: str | None = None
    owasp_category: str | None = None
    first_seen: datetime = None
    last_seen: datetime = None
    false_positive: bool = False
    fixed: bool = False
    fix_time_hours: float | None = None
    developer_id: str | None = None

    def __post_init__(self):
        if not self.first_seen:
            self.first_seen = datetime.now()
        if not self.last_seen:
            self.last_seen = datetime.now()


@dataclass
class SecurityMetrics:
    """مقاييس أمنية شاملة"""

    # Real-time metrics
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    # Velocity metrics
    findings_per_1000_loc: float  # Lines of Code
    new_findings_last_24h: int
    fixed_findings_last_24h: int

    # Quality metrics
    false_positive_rate: float
    mean_time_to_detect: float  # hours
    mean_time_to_fix: float  # hours

    # Risk metrics
    overall_risk_score: float  # 0-100
    security_debt_score: float  # 0-100
    trend_direction: str  # IMPROVING, DEGRADING, STABLE

    # Team metrics
    findings_per_developer: dict[str, int]
    fix_rate_per_developer: dict[str, float]

    timestamp: datetime = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


# ============================================================
# 🧮 ADVANCED ALGORITHMS
# ============================================================


class SecurityMetricsEngine:
    """محرك متقدم لحساب المقاييس الأمنية باستخدام خوارزميات ذكية"""

    def __init__(self):
        self.findings_history: list[SecurityFinding] = []
        self.metrics_history: list[SecurityMetrics] = []

        # Severity weights (CVSS-inspired)
        self.severity_weights = {
            "CRITICAL": 10.0,
            "HIGH": 7.5,
            "MEDIUM": 5.0,
            "LOW": 2.5,
            "INFO": 1.0,
        }

        # CWE risk multipliers
        self.cwe_risk_multipliers = {
            "CWE-89": 2.0,  # SQL Injection
            "CWE-79": 1.8,  # XSS
            "CWE-798": 2.5,  # Hard-coded credentials
            "CWE-327": 1.5,  # Broken crypto
            "CWE-22": 1.7,  # Path traversal
        }

    # --------------------------------------------------------
    # 🎯 ALGORITHM 1: Advanced Risk Scoring (FAANG-style)
    # --------------------------------------------------------

    def calculate_advanced_risk_score(
        self, findings: list[SecurityFinding], code_metrics: dict | None = None
    ) -> float:
        """
        خوارزمية متقدمة لحساب درجة المخاطر
        مستوحاة من: Google's Risk Score, Meta's Security Score

        Formula:
        Risk = Σ(Severity × Age × Exposure × CWE_multiplier) / Normalization_factor
        """
        if not findings:
            return 0.0

        code_metrics = code_metrics or {}
        public_endpoints = code_metrics.get("public_endpoints", 10)

        total_risk = 0.0

        for finding in findings:
            if finding.fixed or finding.false_positive:
                continue

            # 1. Base severity score
            severity_score = self.severity_weights.get(finding.severity, 1.0)

            # 2. Age factor (older = worse)
            age_days = (datetime.now() - finding.first_seen).days
            age_factor = 1 + (age_days / 30.0)  # +1 per month
            age_factor = min(age_factor, 5.0)  # Cap at 5x

            # 3. Exposure factor (how critical is the file?)
            exposure_factor = self._calculate_exposure_factor(finding.file_path, public_endpoints)

            # 4. CWE risk multiplier
            cwe_multiplier = self.cwe_risk_multipliers.get(finding.cwe_id, 1.0)

            # 5. Calculate finding risk
            finding_risk = severity_score * age_factor * exposure_factor * cwe_multiplier

            total_risk += finding_risk

        # Normalize to 0-100 scale
        normalization_factor = len(findings) * 10.0
        risk_score = (total_risk / normalization_factor) * 100
        risk_score = min(risk_score, 100.0)

        return round(risk_score, 2)

    def _calculate_exposure_factor(self, file_path: str, public_endpoints: int) -> float:
        """حساب مدى تعرض الملف للخطر"""
        exposure = 1.0

        # High exposure paths
        high_exposure_patterns = [
            "api/",
            "routes/",
            "views/",
            "controllers/",
            "auth/",
            "login",
            "admin/",
        ]

        for pattern in high_exposure_patterns:
            if pattern in file_path.lower():
                exposure *= 1.5

        # Low exposure paths
        low_exposure_patterns = ["test_", "tests/", "migrations/", "scripts/"]

        for pattern in low_exposure_patterns:
            if pattern in file_path.lower():
                exposure *= 0.5

        return min(exposure, 3.0)

    # --------------------------------------------------------
    # 🔮 ALGORITHM 2: Predictive Analytics
    # --------------------------------------------------------

    def predict_future_risk(
        self, historical_metrics: list[SecurityMetrics], days_ahead: int = 30
    ) -> dict[str, float]:
        """
        تنبؤ بالمخاطر المستقبلية باستخدام Linear Regression
        مثل: Google's Predictive Security, AWS GuardDuty ML
        """
        if len(historical_metrics) < 7:
            return {"predicted_risk": 0.0, "confidence": 0.0, "trend": "INSUFFICIENT_DATA"}

        # Extract time series data
        risk_scores = [m.overall_risk_score for m in historical_metrics[-30:]]

        # Simple linear regression
        n = len(risk_scores)
        x = list(range(n))
        y = risk_scores

        # Calculate slope (trend)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        slope = 0 if denominator == 0 else numerator / denominator

        intercept = y_mean - slope * x_mean

        # Predict future value
        future_x = n + days_ahead
        predicted_risk = slope * future_x + intercept
        predicted_risk = max(0, min(100, predicted_risk))

        # Calculate confidence (based on R²)
        ss_total = sum((y[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))

        r_squared = 0 if ss_total == 0 else 1 - ss_residual / ss_total

        confidence = max(0, min(100, r_squared * 100))

        # Determine trend
        if slope > 0.5:
            trend = "DEGRADING"
        elif slope < -0.5:
            trend = "IMPROVING"
        else:
            trend = "STABLE"

        return {
            "predicted_risk": round(predicted_risk, 2),
            "confidence": round(confidence, 2),
            "trend": trend,
            "slope": round(slope, 4),
            "current_risk": risk_scores[-1],
        }

    # --------------------------------------------------------
    # 🎲 ALGORITHM 3: Anomaly Detection
    # --------------------------------------------------------

    def detect_anomalies(
        self,
        current_metrics: SecurityMetrics,
        historical_metrics: list[SecurityMetrics],
        threshold_std: float = 2.0,
    ) -> list[dict]:
        """
        كشف الشذوذات باستخدام Z-Score
        مثل: DataDog Anomaly Detection, AWS CloudWatch Anomalies
        """
        if len(historical_metrics) < 7:
            return []

        anomalies = []

        # Metrics to check
        metrics_to_check = [
            ("critical_count", "Critical findings"),
            ("new_findings_last_24h", "New findings"),
            ("false_positive_rate", "False positive rate"),
            ("mean_time_to_fix", "Mean time to fix"),
        ]

        for metric_name, display_name in metrics_to_check:
            # Get historical values
            historical_values = [getattr(m, metric_name) for m in historical_metrics[-30:]]

            if not historical_values:
                continue

            # Calculate mean and std
            mean_val = statistics.mean(historical_values)

            if len(historical_values) < 2:
                continue

            std_val = statistics.stdev(historical_values)

            if std_val == 0:
                continue

            # Calculate Z-score for current value
            current_val = getattr(current_metrics, metric_name)
            z_score = (current_val - mean_val) / std_val

            # Check if anomaly
            if abs(z_score) > threshold_std:
                anomalies.append(
                    {
                        "metric": display_name,
                        "current_value": round(current_val, 2),
                        "expected_value": round(mean_val, 2),
                        "z_score": round(z_score, 2),
                        "severity": "HIGH" if abs(z_score) > 3 else "MEDIUM",
                        "direction": "INCREASE" if z_score > 0 else "DECREASE",
                    }
                )

        return anomalies

    # --------------------------------------------------------
    # 🏆 ALGORITHM 4: Developer Performance Scoring
    # --------------------------------------------------------

    def calculate_developer_security_score(
        self, findings: list[SecurityFinding], developer_id: str
    ) -> dict:
        """
        حساب درجة أمان المطور (Gamification)
        مثل: Meta's Developer Scorecard, Google's Code Health
        """
        dev_findings = [f for f in findings if f.developer_id == developer_id]

        if not dev_findings:
            return {
                "developer_id": developer_id,
                "security_score": 100.0,
                "grade": "A+",
                "findings_introduced": 0,
                "findings_fixed": 0,
                "avg_fix_time": 0.0,
            }

        # Calculate metrics
        total_introduced = len([f for f in dev_findings if not f.fixed])
        total_fixed = len([f for f in dev_findings if f.fixed])

        fix_times = [f.fix_time_hours for f in dev_findings if f.fixed and f.fix_time_hours]
        avg_fix_time = statistics.mean(fix_times) if fix_times else 0

        # Calculate score (0-100)
        score = 100.0

        # Penalty for findings (weighted by severity)
        for finding in dev_findings:
            if not finding.fixed:
                penalty = self.severity_weights[finding.severity]
                score -= penalty

        # Bonus for quick fixes
        if avg_fix_time > 0:
            if avg_fix_time < 24:  # Less than 1 day
                score += 5
            elif avg_fix_time > 168:  # More than 1 week
                score -= 5

        # Ensure score is 0-100
        score = max(0, min(100, score))

        # Assign grade
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C"
        else:
            grade = "F"

        return {
            "developer_id": developer_id,
            "security_score": round(score, 2),
            "grade": grade,
            "findings_introduced": total_introduced,
            "findings_fixed": total_fixed,
            "avg_fix_time_hours": round(avg_fix_time, 2),
            "fix_rate": round(total_fixed / len(dev_findings) * 100, 2),
        }

    # --------------------------------------------------------
    # 💰 ALGORITHM 5: Security Debt Calculation
    # --------------------------------------------------------

    def calculate_security_debt(
        self, findings: list[SecurityFinding], hourly_rate: float = 100.0
    ) -> dict:
        """
        حساب الدين الأمني (Security Debt)
        مثل: SonarQube Technical Debt, GitHub Advanced Security

        Formula: Debt = Σ(Estimated_Fix_Time × Hourly_Rate × Risk_Multiplier)
        """

        # Estimated fix time per severity (hours)
        fix_time_estimates = {"CRITICAL": 8.0, "HIGH": 4.0, "MEDIUM": 2.0, "LOW": 1.0, "INFO": 0.5}

        total_debt = 0.0
        debt_by_severity = defaultdict(float)

        for finding in findings:
            if finding.fixed or finding.false_positive:
                continue

            # Base fix time
            fix_time = fix_time_estimates.get(finding.severity, 1.0)

            # Age multiplier (older = more expensive to fix)
            age_days = (datetime.now() - finding.first_seen).days
            age_multiplier = 1 + (age_days / 365.0)  # +1 per year

            # Calculate debt for this finding
            finding_debt = fix_time * hourly_rate * age_multiplier

            total_debt += finding_debt
            debt_by_severity[finding.severity] += finding_debt

        return {
            "total_debt_usd": round(total_debt, 2),
            "debt_by_severity": {k: round(v, 2) for k, v in debt_by_severity.items()},
            "estimated_fix_time_hours": round(
                sum(
                    fix_time_estimates.get(f.severity, 1.0)
                    for f in findings
                    if not f.fixed and not f.false_positive
                ),
                2,
            ),
            "findings_count": len([f for f in findings if not f.fixed and not f.false_positive]),
        }

    # --------------------------------------------------------
    # 📈 ALGORITHM 6: Trend Analysis
    # --------------------------------------------------------

    def analyze_trends(self, metrics_history: list[SecurityMetrics], window_days: int = 30) -> dict:
        """
        تحليل الاتجاهات باستخدام Moving Averages
        مثل: Datadog Trends, Grafana Analytics
        """
        if len(metrics_history) < 2:
            return {"status": "INSUFFICIENT_DATA"}

        recent_metrics = metrics_history[-window_days:]

        # Calculate moving averages
        risk_scores = [m.overall_risk_score for m in recent_metrics]
        ma_7 = self._moving_average(risk_scores, 7)
        ma_30 = self._moving_average(risk_scores, 30)

        # Velocity (rate of change)
        if len(risk_scores) >= 2:
            velocity = risk_scores[-1] - risk_scores[0]
            velocity_per_day = velocity / len(risk_scores)
        else:
            velocity = 0
            velocity_per_day = 0

        # Volatility (standard deviation)
        volatility = statistics.stdev(risk_scores) if len(risk_scores) > 1 else 0

        return {
            "current_risk": risk_scores[-1] if risk_scores else 0,
            "ma_7_days": round(ma_7[-1], 2) if ma_7 else 0,
            "ma_30_days": round(ma_30[-1], 2) if ma_30 else 0,
            "velocity": round(velocity, 2),
            "velocity_per_day": round(velocity_per_day, 2),
            "volatility": round(volatility, 2),
            "trend": self._determine_trend(ma_7, ma_30),
            "data_points": len(risk_scores),
        }

    def _moving_average(self, data: list[float], window: int) -> list[float]:
        """حساب المتوسط المتحرك"""
        if len(data) < window:
            window = len(data)

        result = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            window_data = data[start : i + 1]
            result.append(statistics.mean(window_data))

        return result

    def _determine_trend(self, ma_short: list[float], ma_long: list[float]) -> str:
        """تحديد الاتجاه بناءً على المتوسطات المتحركة"""
        if not ma_short or not ma_long:
            return "UNKNOWN"

        short = ma_short[-1]
        long = ma_long[-1]

        if short > long * 1.05:  # 5% higher
            return "DEGRADING"
        elif short < long * 0.95:  # 5% lower
            return "IMPROVING"
        else:
            return "STABLE"

    # --------------------------------------------------------
    # 🎯 MAIN ANALYTICS FUNCTION
    # --------------------------------------------------------

    def generate_comprehensive_report(
        self, findings: list[SecurityFinding], code_metrics: dict | None = None, hourly_rate: float = 100.0
    ) -> dict:
        """
        توليد تقرير شامل بكل المقاييس والخوارزميات
        """

        # Calculate all metrics
        risk_score = self.calculate_advanced_risk_score(findings, code_metrics)
        security_debt = self.calculate_security_debt(findings, hourly_rate)

        # Get unique developers
        developers = list({f.developer_id for f in findings if f.developer_id})
        developer_scores = {
            dev: self.calculate_developer_security_score(findings, dev) for dev in developers
        }

        # Basic counts
        severity_counts = defaultdict(int)
        for finding in findings:
            if not finding.fixed and not finding.false_positive:
                severity_counts[finding.severity] += 1

        # Calculate fix times
        fix_times = [f.fix_time_hours for f in findings if f.fixed and f.fix_time_hours]

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(findings),
                "open_findings": len([f for f in findings if not f.fixed]),
                "fixed_findings": len([f for f in findings if f.fixed]),
                "false_positives": len([f for f in findings if f.false_positive]),
            },
            "severity_distribution": dict(severity_counts),
            "risk_analysis": {
                "overall_risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
            },
            "security_debt": security_debt,
            "performance_metrics": {
                "mean_time_to_fix_hours": round(statistics.mean(fix_times), 2) if fix_times else 0,
                "median_time_to_fix_hours": (
                    round(statistics.median(fix_times), 2) if fix_times else 0
                ),
                "fastest_fix_hours": round(min(fix_times), 2) if fix_times else 0,
                "slowest_fix_hours": round(max(fix_times), 2) if fix_times else 0,
            },
            "developer_scores": developer_scores,
            "recommendations": self._generate_recommendations(findings, risk_score),
        }

    def _get_risk_level(self, risk_score: float) -> str:
        """تحديد مستوى الخطر"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_recommendations(
        self, findings: list[SecurityFinding], risk_score: float
    ) -> list[str]:
        """توليد توصيات ذكية"""
        recommendations = []

        # Check critical findings
        critical = [f for f in findings if f.severity == "CRITICAL" and not f.fixed]
        if critical:
            recommendations.append(
                f"🚨 URGENT: Fix {len(critical)} critical security issues immediately"
            )

        # Check old findings
        old_findings = [
            f for f in findings if not f.fixed and (datetime.now() - f.first_seen).days > 30
        ]
        if old_findings:
            recommendations.append(f"⏰ Address {len(old_findings)} findings older than 30 days")

        # Check high risk score
        if risk_score > 70:
            recommendations.append("📊 Overall risk score is high - consider security sprint")

        # Check specific CWEs
        sql_injection = [f for f in findings if f.cwe_id == "CWE-89"]
        if sql_injection:
            recommendations.append(
                f"💉 Found {len(sql_injection)} SQL injection risks - prioritize immediately"
            )

        return recommendations


# ============================================================
# 🧪 EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Create engine
    engine = SecurityMetricsEngine()

    # Sample findings
    findings = [
        SecurityFinding(
            id="1",
            severity="CRITICAL",
            rule_id="sql-injection",
            file_path="app/api/routes.py",
            line_number=45,
            message="SQL injection vulnerability",
            cwe_id="CWE-89",
            developer_id="dev_001",
            first_seen=datetime.now() - timedelta(days=15),
        ),
        SecurityFinding(
            id="2",
            severity="HIGH",
            rule_id="hardcoded-secret",
            file_path="app/config.py",
            line_number=12,
            message="Hardcoded API key",
            cwe_id="CWE-798",
            developer_id="dev_002",
            first_seen=datetime.now() - timedelta(days=5),
            fixed=True,
            fix_time_hours=24.0,
        ),
    ]

    # Generate comprehensive report
    report = engine.generate_comprehensive_report(
        findings, code_metrics={"lines_of_code": 50000, "public_endpoints": 25}, hourly_rate=100.0
    )

    print(json.dumps(report, indent=2, default=str))
