"""
🧪 Advanced Security Metrics Engine - Comprehensive Test Suite
===============================================================
Tests for all algorithms and metrics calculations
"""

from datetime import datetime, timedelta

import pytest

from app.services.security_metrics_engine import (SecurityFinding, SecurityMetrics,
                                                  SecurityMetricsEngine)


class TestSecurityFinding:
    """Test SecurityFinding data model"""

    def test_security_finding_creation(self):
        """Test creating a security finding"""
        finding = SecurityFinding(
            id="test-1",
            severity="CRITICAL",
            rule_id="sql-injection",
            file_path="app/api/routes.py",
            line_number=42,
            message="SQL injection detected",
            cwe_id="CWE-89",
        )

        assert finding.id == "test-1"
        assert finding.severity == "CRITICAL"
        assert finding.rule_id == "sql-injection"
        assert finding.file_path == "app/api/routes.py"
        assert finding.line_number == 42
        assert finding.message == "SQL injection detected"
        assert finding.cwe_id == "CWE-89"
        assert finding.first_seen is not None
        assert finding.last_seen is not None
        assert finding.fixed is False
        assert finding.false_positive is False

    def test_security_finding_with_timestamps(self):
        """Test security finding with custom timestamps"""
        now = datetime.now()
        finding = SecurityFinding(
            id="test-2",
            severity="HIGH",
            rule_id="xss",
            file_path="app/views.py",
            line_number=10,
            message="XSS vulnerability",
            first_seen=now - timedelta(days=7),
            last_seen=now,
        )

        assert finding.first_seen == now - timedelta(days=7)
        assert finding.last_seen == now


class TestSecurityMetricsEngine:
    """Test SecurityMetricsEngine algorithms"""

    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return SecurityMetricsEngine()

    @pytest.fixture
    def sample_findings(self):
        """Create sample findings for testing"""
        now = datetime.now()
        return [
            SecurityFinding(
                id="1",
                severity="CRITICAL",
                rule_id="sql-injection",
                file_path="app/api/routes.py",
                line_number=45,
                message="SQL injection vulnerability",
                cwe_id="CWE-89",
                developer_id="dev_001",
                first_seen=now - timedelta(days=15),
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
                first_seen=now - timedelta(days=5),
                fixed=True,
                fix_time_hours=24.0,
            ),
            SecurityFinding(
                id="3",
                severity="MEDIUM",
                rule_id="weak-crypto",
                file_path="app/services/encryption.py",
                line_number=88,
                message="Weak cryptographic algorithm",
                cwe_id="CWE-327",
                developer_id="dev_001",
                first_seen=now - timedelta(days=2),
            ),
            SecurityFinding(
                id="4",
                severity="LOW",
                rule_id="info-leak",
                file_path="app/utils/logger.py",
                line_number=33,
                message="Information disclosure in logs",
                developer_id="dev_003",
                first_seen=now - timedelta(days=1),
            ),
        ]

    # --------------------------------------------------------
    # Test Algorithm 1: Advanced Risk Scoring
    # --------------------------------------------------------

    def test_calculate_advanced_risk_score_empty_findings(self, engine):
        """Test risk score with no findings"""
        risk_score = engine.calculate_advanced_risk_score([])
        assert risk_score == 0.0

    def test_calculate_advanced_risk_score_basic(self, engine, sample_findings):
        """Test basic risk score calculation"""
        risk_score = engine.calculate_advanced_risk_score(
            sample_findings, code_metrics={"lines_of_code": 50000, "public_endpoints": 25}
        )

        assert isinstance(risk_score, float)
        assert 0 <= risk_score <= 100

    def test_calculate_advanced_risk_score_ignores_fixed(self, engine):
        """Test that fixed findings are ignored in risk calculation"""
        findings = [
            SecurityFinding(
                id="1",
                severity="CRITICAL",
                rule_id="sql-injection",
                file_path="app/api/routes.py",
                line_number=45,
                message="SQL injection",
                fixed=True,
            )
        ]

        risk_score = engine.calculate_advanced_risk_score(findings)
        assert risk_score == 0.0

    def test_calculate_advanced_risk_score_ignores_false_positives(self, engine):
        """Test that false positives are ignored"""
        findings = [
            SecurityFinding(
                id="1",
                severity="CRITICAL",
                rule_id="sql-injection",
                file_path="app/api/routes.py",
                line_number=45,
                message="SQL injection",
                false_positive=True,
            )
        ]

        risk_score = engine.calculate_advanced_risk_score(findings)
        assert risk_score == 0.0

    def test_calculate_exposure_factor_high_exposure_paths(self, engine):
        """Test exposure factor for high-risk paths"""
        exposure = engine._calculate_exposure_factor("app/api/auth/login.py", 10)
        assert exposure > 1.0

        exposure = engine._calculate_exposure_factor("app/routes/admin.py", 10)
        assert exposure > 1.0

    def test_calculate_exposure_factor_low_exposure_paths(self, engine):
        """Test exposure factor for low-risk paths"""
        exposure = engine._calculate_exposure_factor("tests/test_api.py", 10)
        assert exposure < 1.0

        exposure = engine._calculate_exposure_factor("migrations/version_001.py", 10)
        assert exposure < 1.0

    # --------------------------------------------------------
    # Test Algorithm 2: Predictive Analytics
    # --------------------------------------------------------

    def test_predict_future_risk_insufficient_data(self, engine):
        """Test prediction with insufficient data"""
        historical = [
            SecurityMetrics(
                total_findings=5,
                critical_count=1,
                high_count=2,
                medium_count=1,
                low_count=1,
                findings_per_1000_loc=1.0,
                new_findings_last_24h=0,
                fixed_findings_last_24h=0,
                false_positive_rate=0.0,
                mean_time_to_detect=1.0,
                mean_time_to_fix=24.0,
                overall_risk_score=50.0,
                security_debt_score=30.0,
                trend_direction="STABLE",
                findings_per_developer={},
                fix_rate_per_developer={},
            )
        ]

        prediction = engine.predict_future_risk(historical)
        assert prediction["trend"] == "INSUFFICIENT_DATA"
        assert prediction["confidence"] == 0.0

    def test_predict_future_risk_with_data(self, engine):
        """Test prediction with sufficient data"""
        # Create 10 days of metrics with increasing risk
        historical = []
        for i in range(10):
            historical.append(
                SecurityMetrics(
                    total_findings=5 + i,
                    critical_count=i,
                    high_count=2,
                    medium_count=1,
                    low_count=1,
                    findings_per_1000_loc=1.0,
                    new_findings_last_24h=1,
                    fixed_findings_last_24h=0,
                    false_positive_rate=0.0,
                    mean_time_to_detect=1.0,
                    mean_time_to_fix=24.0,
                    overall_risk_score=40.0 + i * 2,
                    security_debt_score=30.0,
                    trend_direction="DEGRADING",
                    findings_per_developer={},
                    fix_rate_per_developer={},
                )
            )

        prediction = engine.predict_future_risk(historical, days_ahead=7)

        assert "predicted_risk" in prediction
        assert "confidence" in prediction
        assert "trend" in prediction
        assert 0 <= prediction["predicted_risk"] <= 100
        assert 0 <= prediction["confidence"] <= 100
        assert prediction["trend"] in ["DEGRADING", "IMPROVING", "STABLE"]

    # --------------------------------------------------------
    # Test Algorithm 3: Anomaly Detection
    # --------------------------------------------------------

    def test_detect_anomalies_insufficient_data(self, engine):
        """Test anomaly detection with insufficient data"""
        current = SecurityMetrics(
            total_findings=5,
            critical_count=1,
            high_count=2,
            medium_count=1,
            low_count=1,
            findings_per_1000_loc=1.0,
            new_findings_last_24h=0,
            fixed_findings_last_24h=0,
            false_positive_rate=0.0,
            mean_time_to_detect=1.0,
            mean_time_to_fix=24.0,
            overall_risk_score=50.0,
            security_debt_score=30.0,
            trend_direction="STABLE",
            findings_per_developer={},
            fix_rate_per_developer={},
        )

        anomalies = engine.detect_anomalies(current, [])
        assert anomalies == []

    def test_detect_anomalies_with_spike(self, engine):
        """Test anomaly detection with a spike in findings"""
        # Create baseline metrics with some variation
        historical = []
        for i in range(30):
            # Add some variation to avoid std=0
            variation = (i % 3) - 1  # -1, 0, 1 pattern
            historical.append(
                SecurityMetrics(
                    total_findings=5 + variation,
                    critical_count=1 + variation,  # Varies between 0 and 2
                    high_count=2 + variation,
                    medium_count=1,
                    low_count=1,
                    findings_per_1000_loc=1.0,
                    new_findings_last_24h=2 + variation,  # Varies between 1 and 3
                    fixed_findings_last_24h=2,
                    false_positive_rate=0.1,
                    mean_time_to_detect=1.0,
                    mean_time_to_fix=24.0 + variation,  # Varies between 23 and 25
                    overall_risk_score=30.0,
                    security_debt_score=20.0,
                    trend_direction="STABLE",
                    findings_per_developer={},
                    fix_rate_per_developer={},
                )
            )

        # Create current metrics with spike (much larger to ensure anomaly detection)
        current = SecurityMetrics(
            total_findings=50,
            critical_count=30,  # Much larger spike (was 1, now 30)
            high_count=10,
            medium_count=5,
            low_count=5,
            findings_per_1000_loc=1.0,
            new_findings_last_24h=45,  # Much larger spike (was 2, now 45)
            fixed_findings_last_24h=0,
            false_positive_rate=0.1,
            mean_time_to_detect=1.0,
            mean_time_to_fix=100.0,  # Much larger spike (was 24, now 100)
            overall_risk_score=95.0,
            security_debt_score=90.0,
            trend_direction="DEGRADING",
            findings_per_developer={},
            fix_rate_per_developer={},
        )

        anomalies = engine.detect_anomalies(current, historical, threshold_std=2.0)

        # Should detect anomalies in critical_count and new_findings
        assert len(anomalies) > 0
        # At least one of the metrics should be flagged as anomalous
        assert any(
            a["metric"] in ["Critical findings", "New findings", "Mean time to fix"]
            for a in anomalies
        )

    # --------------------------------------------------------
    # Test Algorithm 4: Developer Performance Scoring
    # --------------------------------------------------------

    def test_developer_score_no_findings(self, engine):
        """Test developer score with no findings"""
        score = engine.calculate_developer_security_score([], "dev_999")

        assert score["developer_id"] == "dev_999"
        assert score["security_score"] == 100.0
        assert score["grade"] == "A+"
        assert score["findings_introduced"] == 0
        assert score["findings_fixed"] == 0

    def test_developer_score_with_findings(self, engine, sample_findings):
        """Test developer score calculation"""
        score = engine.calculate_developer_security_score(sample_findings, "dev_001")

        assert score["developer_id"] == "dev_001"
        assert isinstance(score["security_score"], float)
        assert 0 <= score["security_score"] <= 100
        assert score["grade"] in ["A+", "A", "B", "C", "F"]
        assert score["findings_introduced"] > 0

    def test_developer_score_grading(self, engine):
        """Test grading system"""
        # Create findings with different severities for different developers
        findings = [
            SecurityFinding(
                id="1",
                severity="INFO",
                rule_id="info",
                file_path="test.py",
                line_number=1,
                message="Info",
                developer_id="dev_good",
            ),
            SecurityFinding(
                id="2",
                severity="CRITICAL",
                rule_id="critical",
                file_path="test.py",
                line_number=1,
                message="Critical",
                developer_id="dev_bad",
            ),
        ]

        good_score = engine.calculate_developer_security_score(findings, "dev_good")
        bad_score = engine.calculate_developer_security_score(findings, "dev_bad")

        # Developer with INFO should have better score than CRITICAL
        assert good_score["security_score"] > bad_score["security_score"]

    # --------------------------------------------------------
    # Test Algorithm 5: Security Debt Calculation
    # --------------------------------------------------------

    def test_security_debt_no_findings(self, engine):
        """Test security debt with no findings"""
        debt = engine.calculate_security_debt([])

        assert debt["total_debt_usd"] == 0.0
        assert debt["findings_count"] == 0
        assert debt["estimated_fix_time_hours"] == 0.0

    def test_security_debt_calculation(self, engine, sample_findings):
        """Test security debt calculation"""
        debt = engine.calculate_security_debt(sample_findings, hourly_rate=100.0)

        assert debt["total_debt_usd"] > 0.0
        assert "debt_by_severity" in debt
        assert debt["findings_count"] > 0
        assert debt["estimated_fix_time_hours"] > 0.0

    def test_security_debt_ignores_fixed(self, engine):
        """Test that security debt ignores fixed findings"""
        findings = [
            SecurityFinding(
                id="1",
                severity="CRITICAL",
                rule_id="sql-injection",
                file_path="app/api/routes.py",
                line_number=45,
                message="SQL injection",
                fixed=True,
            ),
            SecurityFinding(
                id="2",
                severity="HIGH",
                rule_id="xss",
                file_path="app/views.py",
                line_number=10,
                message="XSS",
                fixed=False,
            ),
        ]

        debt = engine.calculate_security_debt(findings)

        # Should only count the HIGH severity finding
        assert debt["findings_count"] == 1
        assert "HIGH" in debt["debt_by_severity"]
        assert "CRITICAL" not in debt["debt_by_severity"]

    def test_security_debt_age_multiplier(self, engine):
        """Test that older findings have higher debt"""
        now = datetime.now()

        findings_new = [
            SecurityFinding(
                id="1",
                severity="HIGH",
                rule_id="test",
                file_path="test.py",
                line_number=1,
                message="Test",
                first_seen=now,
            )
        ]

        findings_old = [
            SecurityFinding(
                id="1",
                severity="HIGH",
                rule_id="test",
                file_path="test.py",
                line_number=1,
                message="Test",
                first_seen=now - timedelta(days=365),
            )
        ]

        debt_new = engine.calculate_security_debt(findings_new)
        debt_old = engine.calculate_security_debt(findings_old)

        # Older finding should have higher debt
        assert debt_old["total_debt_usd"] > debt_new["total_debt_usd"]

    # --------------------------------------------------------
    # Test Algorithm 6: Trend Analysis
    # --------------------------------------------------------

    def test_analyze_trends_insufficient_data(self, engine):
        """Test trend analysis with insufficient data"""
        trends = engine.analyze_trends([])
        assert trends["status"] == "INSUFFICIENT_DATA"

    def test_analyze_trends_with_data(self, engine):
        """Test trend analysis with sufficient data"""
        # Create 30 days of metrics
        metrics_history = []
        for i in range(30):
            metrics_history.append(
                SecurityMetrics(
                    total_findings=5,
                    critical_count=1,
                    high_count=2,
                    medium_count=1,
                    low_count=1,
                    findings_per_1000_loc=1.0,
                    new_findings_last_24h=0,
                    fixed_findings_last_24h=0,
                    false_positive_rate=0.0,
                    mean_time_to_detect=1.0,
                    mean_time_to_fix=24.0,
                    overall_risk_score=40.0 + i,
                    security_debt_score=30.0,
                    trend_direction="STABLE",
                    findings_per_developer={},
                    fix_rate_per_developer={},
                )
            )

        trends = engine.analyze_trends(metrics_history)

        assert "current_risk" in trends
        assert "ma_7_days" in trends
        assert "ma_30_days" in trends
        assert "velocity" in trends
        assert "trend" in trends
        assert trends["trend"] in ["DEGRADING", "IMPROVING", "STABLE", "UNKNOWN"]

    def test_moving_average_calculation(self, engine):
        """Test moving average calculation"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ma = engine._moving_average(data, 3)

        assert len(ma) == len(data)
        # Last value should be average of last 3 values: (8+9+10)/3 = 9
        assert ma[-1] == 9.0

    def test_determine_trend(self, engine):
        """Test trend determination"""
        # Degrading trend: short MA > long MA
        trend = engine._determine_trend([60.0], [50.0])
        assert trend == "DEGRADING"

        # Improving trend: short MA < long MA
        trend = engine._determine_trend([40.0], [50.0])
        assert trend == "IMPROVING"

        # Stable trend: MAs are close
        trend = engine._determine_trend([50.0], [51.0])
        assert trend == "STABLE"

    # --------------------------------------------------------
    # Test Comprehensive Report Generation
    # --------------------------------------------------------

    def test_generate_comprehensive_report(self, engine, sample_findings):
        """Test comprehensive report generation"""
        report = engine.generate_comprehensive_report(
            sample_findings,
            code_metrics={"lines_of_code": 50000, "public_endpoints": 25},
            hourly_rate=100.0,
        )

        assert "timestamp" in report
        assert "summary" in report
        assert "severity_distribution" in report
        assert "risk_analysis" in report
        assert "security_debt" in report
        assert "performance_metrics" in report
        assert "developer_scores" in report
        assert "recommendations" in report

        # Check summary
        assert report["summary"]["total_findings"] == len(sample_findings)
        assert report["summary"]["open_findings"] > 0
        assert report["summary"]["fixed_findings"] > 0

        # Check risk analysis
        assert "overall_risk_score" in report["risk_analysis"]
        assert "risk_level" in report["risk_analysis"]

        # Check developer scores
        assert len(report["developer_scores"]) > 0

    def test_get_risk_level(self, engine):
        """Test risk level classification"""
        assert engine._get_risk_level(90) == "CRITICAL"
        assert engine._get_risk_level(70) == "HIGH"
        assert engine._get_risk_level(50) == "MEDIUM"
        assert engine._get_risk_level(30) == "LOW"
        assert engine._get_risk_level(10) == "MINIMAL"

    def test_generate_recommendations(self, engine):
        """Test recommendation generation"""
        now = datetime.now()

        findings = [
            SecurityFinding(
                id="1",
                severity="CRITICAL",
                rule_id="sql-injection",
                file_path="app/api/routes.py",
                line_number=45,
                message="SQL injection",
                cwe_id="CWE-89",
                first_seen=now - timedelta(days=60),
            ),
            SecurityFinding(
                id="2",
                severity="HIGH",
                rule_id="xss",
                file_path="app/views.py",
                line_number=10,
                message="XSS",
                first_seen=now - timedelta(days=45),
            ),
        ]

        recommendations = engine._generate_recommendations(findings, 75.0)

        # Should recommend fixing critical issues
        assert any("critical" in r.lower() for r in recommendations)
        # Should recommend addressing old findings
        assert any("30 days" in r for r in recommendations)
        # Should recommend security sprint for high risk
        assert any("security sprint" in r.lower() for r in recommendations)
        # Should recommend addressing SQL injection
        assert any("sql injection" in r.lower() for r in recommendations)


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_complete_workflow(self):
        """Test a complete analysis workflow"""
        engine = SecurityMetricsEngine()
        now = datetime.now()

        # Create findings
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
                first_seen=now - timedelta(days=15),
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
                first_seen=now - timedelta(days=5),
                fixed=True,
                fix_time_hours=24.0,
            ),
            SecurityFinding(
                id="3",
                severity="MEDIUM",
                rule_id="weak-crypto",
                file_path="app/services/encryption.py",
                line_number=88,
                message="Weak cryptographic algorithm",
                cwe_id="CWE-327",
                developer_id="dev_001",
                first_seen=now - timedelta(days=2),
            ),
        ]

        # Generate report
        report = engine.generate_comprehensive_report(
            findings,
            code_metrics={"lines_of_code": 50000, "public_endpoints": 25},
            hourly_rate=100.0,
        )

        # Verify report completeness
        assert report["summary"]["total_findings"] == 3
        assert report["summary"]["open_findings"] == 2
        assert report["summary"]["fixed_findings"] == 1
        assert report["risk_analysis"]["overall_risk_score"] > 0
        assert report["security_debt"]["total_debt_usd"] > 0
        assert len(report["developer_scores"]) == 2  # Two developers
        assert len(report["recommendations"]) > 0

    def test_trend_analysis_workflow(self):
        """Test trend analysis with historical data"""
        engine = SecurityMetricsEngine()

        # Create 14 days of improving metrics
        metrics_history = []
        for i in range(14):
            metrics_history.append(
                SecurityMetrics(
                    total_findings=10 - i,
                    critical_count=max(0, 3 - i // 5),
                    high_count=max(0, 4 - i // 4),
                    medium_count=2,
                    low_count=1,
                    findings_per_1000_loc=1.0,
                    new_findings_last_24h=0,
                    fixed_findings_last_24h=1,
                    false_positive_rate=0.05,
                    mean_time_to_detect=2.0,
                    mean_time_to_fix=20.0,
                    overall_risk_score=70.0 - i * 3,
                    security_debt_score=50.0 - i * 2,
                    trend_direction="IMPROVING",
                    findings_per_developer={},
                    fix_rate_per_developer={},
                )
            )

        # Analyze trends
        trends = engine.analyze_trends(metrics_history)

        assert trends["trend"] == "IMPROVING"
        assert trends["velocity"] < 0  # Negative velocity means improving

    def test_anomaly_detection_workflow(self):
        """Test anomaly detection with spike"""
        engine = SecurityMetricsEngine()

        # Create 30 days of normal metrics with variation
        historical = []
        for i in range(30):
            # Add variation to avoid std=0
            variation = (i % 3) - 1  # -1, 0, 1 pattern
            historical.append(
                SecurityMetrics(
                    total_findings=5 + variation,
                    critical_count=1 + variation,  # Varies between 0 and 2
                    high_count=2 + variation,
                    medium_count=1,
                    low_count=1,
                    findings_per_1000_loc=1.0,
                    new_findings_last_24h=2 + variation,  # Varies between 1 and 3
                    fixed_findings_last_24h=2,
                    false_positive_rate=0.1,
                    mean_time_to_detect=1.0,
                    mean_time_to_fix=24.0 + variation,  # Varies between 23 and 25
                    overall_risk_score=30.0,
                    security_debt_score=20.0,
                    trend_direction="STABLE",
                    findings_per_developer={},
                    fix_rate_per_developer={},
                )
            )

        # Create anomalous current state (much larger spike to ensure detection)
        current = SecurityMetrics(
            total_findings=50,
            critical_count=40,  # Much larger spike
            high_count=8,
            medium_count=1,
            low_count=1,
            findings_per_1000_loc=1.0,
            new_findings_last_24h=45,  # Much larger spike
            fixed_findings_last_24h=0,
            false_positive_rate=0.1,
            mean_time_to_detect=1.0,
            mean_time_to_fix=100.0,  # Much larger spike
            overall_risk_score=95.0,
            security_debt_score=90.0,
            trend_direction="DEGRADING",
            findings_per_developer={},
            fix_rate_per_developer={},
        )

        # Detect anomalies
        anomalies = engine.detect_anomalies(current, historical, threshold_std=2.0)

        assert len(anomalies) > 0
        assert any(a["severity"] in ["HIGH", "MEDIUM"] for a in anomalies)
        # Verify at least one of the key metrics is detected as anomalous
        assert any(
            a["metric"] in ["Critical findings", "New findings", "Mean time to fix"]
            for a in anomalies
        )
