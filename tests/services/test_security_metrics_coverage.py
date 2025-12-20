import pytest
from datetime import datetime, timedelta
from app.services.security_metrics.domain.models import SecurityFinding, Severity, SecurityMetrics, TrendDirection, RiskPrediction
from app.services.security_metrics.application.metrics_calculator import ComprehensiveMetricsCalculator
from app.services.security_metrics.application.risk_calculator import AdvancedRiskCalculator
from app.services.security_metrics.application.predictive_analytics import LinearRegressionPredictor
from app.services.security_metrics.infrastructure.in_memory_repositories import InMemoryFindingsRepository, InMemoryMetricsRepository
from app.services.security_metrics.facade import SecurityMetricsEngine, get_security_metrics_engine

# --- Calculator Tests ---
@pytest.fixture
def calculator():
    return ComprehensiveMetricsCalculator()

def test_metrics_calculator_empty(calculator):
    metrics = calculator.calculate_metrics([])
    assert metrics.total_findings == 0
    assert metrics.critical_count == 0
    assert metrics.findings_per_1000_loc == 0.0

def test_metrics_calculator_basic_counts(calculator):
    findings = [
        SecurityFinding(
            id="1", severity=Severity.CRITICAL, rule_id="rule1", file_path="a.py", line_number=1, message="msg",
            fixed=False, false_positive=False
        ),
        SecurityFinding(
            id="2", severity=Severity.HIGH, rule_id="rule2", file_path="b.py", line_number=1, message="msg",
            fixed=False, false_positive=False
        ),
    ]
    metrics = calculator.calculate_metrics(findings, code_metrics={"lines_of_code": 1000})
    assert metrics.total_findings == 2
    assert metrics.critical_count == 1
    assert metrics.high_count == 1
    assert metrics.medium_count == 0
    assert metrics.findings_per_1000_loc == 2.0  # (2/1000)*1000

def test_velocity_metrics(calculator):
    now = datetime.now()
    findings = [
        SecurityFinding(
            id="1", severity=Severity.LOW, rule_id="rule1", file_path="a.py", line_number=1, message="msg",
            first_seen=now - timedelta(minutes=1), # New in last 24h
            fixed=False
        ),
        SecurityFinding(
            id="2", severity=Severity.LOW, rule_id="rule2", file_path="b.py", line_number=1, message="msg",
            first_seen=now - timedelta(hours=48), # Old
            fixed=True,
            last_seen=now - timedelta(minutes=1) # Fixed in last 24h
        )
    ]
    metrics = calculator.calculate_metrics(findings)
    assert metrics.new_findings_last_24h == 1
    assert metrics.fixed_findings_last_24h == 1

def test_quality_metrics(calculator):
    findings = [
        SecurityFinding(
            id="1", severity=Severity.LOW, rule_id="rule1", file_path="a.py", line_number=1, message="msg",
            false_positive=True
        ),
        SecurityFinding(
            id="2", severity=Severity.LOW, rule_id="rule2", file_path="b.py", line_number=1, message="msg",
            false_positive=False,
            fixed=True,
            fix_time_hours=10.0
        ),
        SecurityFinding(
            id="3", severity=Severity.LOW, rule_id="rule3", file_path="c.py", line_number=1, message="msg",
            false_positive=False,
            fixed=True,
            fix_time_hours=20.0
        )
    ]
    metrics = calculator.calculate_metrics(findings)
    assert metrics.false_positive_rate == round(1/3 * 100, 2)
    assert metrics.mean_time_to_fix == 15.0

def test_team_metrics(calculator):
    findings = [
        SecurityFinding(
            id="1", severity=Severity.LOW, rule_id="r1", file_path="a.py", line_number=1, message="m",
            developer_id="dev1", fixed=True
        ),
        SecurityFinding(
            id="2", severity=Severity.LOW, rule_id="r2", file_path="b.py", line_number=1, message="m",
            developer_id="dev1", fixed=False
        ),
        SecurityFinding(
            id="3", severity=Severity.LOW, rule_id="r3", file_path="c.py", line_number=1, message="m",
            developer_id="dev2", fixed=True
        )
    ]
    metrics = calculator.calculate_metrics(findings)
    assert metrics.findings_per_developer["dev1"] == 2
    assert metrics.findings_per_developer["dev2"] == 1
    assert metrics.fix_rate_per_developer["dev1"] == 50.0
    assert metrics.fix_rate_per_developer["dev2"] == 100.0

# --- Risk Calculator Tests ---
@pytest.fixture
def risk_calculator():
    return AdvancedRiskCalculator()

def test_risk_calculator_empty(risk_calculator):
    assert risk_calculator.calculate_risk_score([]) == 0.0

def test_risk_calculator_basic(risk_calculator):
    now = datetime.now()
    findings = [
        SecurityFinding(
            id="1", severity=Severity.CRITICAL, rule_id="r1", file_path="api/auth.py", line_number=1, message="m",
            first_seen=now - timedelta(days=5),
            cwe_id="CWE-89" # SQL Injection
        ),
        SecurityFinding(
            id="2", severity=Severity.LOW, rule_id="r2", file_path="tests/test_x.py", line_number=1, message="m",
            first_seen=now,
            cwe_id="CWE-000"
        )
    ]
    score = risk_calculator.calculate_risk_score(findings)
    assert score > 0
    assert score <= 100

def test_risk_calculator_exposure_logic(risk_calculator):
    assert risk_calculator.calculate_exposure_factor("api/v1/users.py", 10) > 1.0
    assert risk_calculator.calculate_exposure_factor("tests/unit/test.py", 10) < 1.0
    assert risk_calculator.calculate_exposure_factor("utils/helper.py", 10) == 1.0

# --- Predictive Analytics Tests ---
@pytest.fixture
def predictor():
    return LinearRegressionPredictor()

def test_predictor_not_enough_data(predictor):
    metrics = [] # Empty
    prediction = predictor.predict_future_risk(metrics)
    assert prediction.predicted_risk == 0.0
    assert prediction.confidence == 0.0

def test_predictor_linear_trend(predictor):
    # Create a perfectly increasing risk trend
    metrics = []
    for i in range(30):
        m = SecurityMetrics(
            total_findings=i, critical_count=0, high_count=0, medium_count=0, low_count=0,
            findings_per_1000_loc=0, new_findings_last_24h=0, fixed_findings_last_24h=0,
            false_positive_rate=0, mean_time_to_detect=0, mean_time_to_fix=0,
            overall_risk_score=float(i), # Risk increases by 1 each day
            security_debt_score=0, trend_direction=TrendDirection.STABLE,
            findings_per_developer={}, fix_rate_per_developer={},
            timestamp=datetime.now() - timedelta(days=30-i)
        )
        metrics.append(m)

    prediction = predictor.predict_future_risk(metrics, days_ahead=1)
    assert 29.0 <= prediction.predicted_risk <= 31.0
    assert prediction.trend == TrendDirection.DEGRADING
    assert prediction.confidence > 90.0

def test_predictor_decreasing_trend(predictor):
    metrics = []
    for i in range(30):
        m = SecurityMetrics(
            total_findings=i, critical_count=0, high_count=0, medium_count=0, low_count=0,
            findings_per_1000_loc=0, new_findings_last_24h=0, fixed_findings_last_24h=0,
            false_positive_rate=0, mean_time_to_detect=0, mean_time_to_fix=0,
            overall_risk_score=float(30 - i),
            security_debt_score=0, trend_direction=TrendDirection.STABLE,
            findings_per_developer={}, fix_rate_per_developer={},
            timestamp=datetime.now() - timedelta(days=30-i)
        )
        metrics.append(m)
    prediction = predictor.predict_future_risk(metrics)
    assert prediction.trend == TrendDirection.IMPROVING

# --- Infrastructure / Repository Tests ---
def test_in_memory_findings_repo():
    repo = InMemoryFindingsRepository()
    finding = SecurityFinding(id="f1", severity=Severity.HIGH, rule_id="r", file_path="p", line_number=1, message="m")
    repo.save_finding(finding)

    assert len(repo.get_findings()) == 1
    assert repo.get_findings({"severity": Severity.HIGH})[0].id == "f1"
    assert len(repo.get_findings({"severity": Severity.LOW})) == 0

    repo.update_finding("f1", {"fixed": True})
    assert repo.get_findings()[0].fixed is True

def test_in_memory_metrics_repo():
    repo = InMemoryMetricsRepository()
    m = SecurityMetrics(
        total_findings=0, critical_count=0, high_count=0, medium_count=0, low_count=0,
        findings_per_1000_loc=0, new_findings_last_24h=0, fixed_findings_last_24h=0,
        false_positive_rate=0, mean_time_to_detect=0, mean_time_to_fix=0,
        overall_risk_score=0, security_debt_score=0, trend_direction=TrendDirection.STABLE,
        findings_per_developer={}, fix_rate_per_developer={}
    )
    repo.save_metrics(m)
    assert len(repo.get_historical_metrics(30)) == 1
    # Check that a very small window works if we are fast enough, but 30 days is the standard test
    # To test filtering, we'd need to mock time, but let's stick to behavioral

# --- Facade Tests ---
def test_facade():
    engine = SecurityMetricsEngine()
    finding = SecurityFinding(id="f1", severity=Severity.HIGH, rule_id="r", file_path="p", line_number=1, message="m")

    engine.add_finding(finding)
    assert len(engine.get_findings()) == 1

    risk = engine.calculate_advanced_risk_score([finding])
    assert risk > 0

    prediction = engine.predict_future_risk([])
    assert prediction.predicted_risk == 0.0

    m = SecurityMetrics(
        total_findings=0, critical_count=0, high_count=0, medium_count=0, low_count=0,
        findings_per_1000_loc=0, new_findings_last_24h=0, fixed_findings_last_24h=0,
        false_positive_rate=0, mean_time_to_detect=0, mean_time_to_fix=0,
        overall_risk_score=0, security_debt_score=0, trend_direction=TrendDirection.STABLE,
        findings_per_developer={}, fix_rate_per_developer={}
    )
    engine.save_metrics(m)
    assert len(engine.get_historical_metrics()) == 1

def test_singleton():
    s1 = get_security_metrics_engine()
    s2 = get_security_metrics_engine()
    assert s1 is s2
