# 🚀 Security Metrics & Analytics Engine

## Overview

The Security Metrics & Analytics Engine is a world-class security analysis system inspired by the security platforms of Google, Meta, Microsoft, OpenAI, Apple, and Amazon. It provides advanced algorithms for risk scoring, predictive analytics, anomaly detection, and comprehensive security reporting.

## 🎯 Features

### 1. **Advanced Risk Scoring (FAANG-style)**
- Multi-factor risk calculation using severity, age, exposure, and CWE multipliers
- CVSS-inspired severity weights
- Path-based exposure analysis (api/, auth/, admin/ = higher risk)
- Age amplification (older findings carry higher risk)
- Normalized 0-100 risk scores

### 2. **Predictive Analytics**
- Linear regression-based future risk prediction
- Confidence scoring using R² methodology
- Trend classification (DEGRADING, IMPROVING, STABLE)
- Configurable prediction horizon (default: 30 days)

### 3. **Anomaly Detection**
- Z-Score based statistical anomaly detection
- Configurable threshold (default: 2 standard deviations)
- Multi-metric analysis (critical findings, new findings, fix times, false positive rate)
- Severity classification (HIGH, MEDIUM)

### 4. **Developer Performance Scoring**
- Gamification with letter grades (A+ to F)
- Weighted penalty system based on severity
- Time-to-fix bonus/penalty system
- Fix rate tracking
- Individual developer scorecards

### 5. **Security Debt Calculation**
- Financial impact analysis in USD
- Time-based cost estimation
- Age multiplier for technical debt
- Severity-based breakdown
- Estimated fix time calculation

### 6. **Trend Analysis**
- Moving average calculations (7-day and 30-day)
- Velocity and volatility metrics
- Trend direction determination
- Historical comparison

## 📊 Data Models

### SecurityFinding

Represents a single security finding from code analysis.

```python
@dataclass
class SecurityFinding:
    id: str                          # Unique identifier
    severity: str                    # CRITICAL, HIGH, MEDIUM, LOW, INFO
    rule_id: str                     # Security rule that triggered
    file_path: str                   # File location
    line_number: int                 # Line number in file
    message: str                     # Finding description
    cwe_id: Optional[str]            # CWE identifier (e.g., CWE-89)
    owasp_category: Optional[str]    # OWASP category
    first_seen: datetime             # When first detected
    last_seen: datetime              # Last seen timestamp
    false_positive: bool             # False positive flag
    fixed: bool                      # Fix status
    fix_time_hours: Optional[float]  # Time taken to fix
    developer_id: Optional[str]      # Developer responsible
```

### SecurityMetrics

Comprehensive security metrics snapshot.

```python
@dataclass
class SecurityMetrics:
    # Real-time metrics
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    # Velocity metrics
    findings_per_1000_loc: float
    new_findings_last_24h: int
    fixed_findings_last_24h: int
    
    # Quality metrics
    false_positive_rate: float
    mean_time_to_detect: float
    mean_time_to_fix: float
    
    # Risk metrics
    overall_risk_score: float
    security_debt_score: float
    trend_direction: str
    
    # Team metrics
    findings_per_developer: Dict[str, int]
    fix_rate_per_developer: Dict[str, float]
    
    timestamp: datetime
```

## 🔧 Usage Examples

### Basic Risk Scoring

```python
from datetime import datetime, timedelta
from app.services.security_metrics_engine import (
    SecurityFinding,
    SecurityMetricsEngine
)

# Create engine
engine = SecurityMetricsEngine()

# Create sample findings
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
        first_seen=datetime.now() - timedelta(days=15)
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
        fix_time_hours=24.0
    )
]

# Calculate risk score
risk_score = engine.calculate_advanced_risk_score(
    findings,
    code_metrics={'lines_of_code': 50000, 'public_endpoints': 25}
)
print(f"Risk Score: {risk_score}/100")
```

### Comprehensive Report Generation

```python
# Generate complete analysis report
report = engine.generate_comprehensive_report(
    findings,
    code_metrics={'lines_of_code': 50000, 'public_endpoints': 25},
    hourly_rate=100.0
)

# Access report sections
print(f"Total Findings: {report['summary']['total_findings']}")
print(f"Risk Level: {report['risk_analysis']['risk_level']}")
print(f"Security Debt: ${report['security_debt']['total_debt_usd']}")
print(f"Recommendations: {report['recommendations']}")
```

### Predictive Analytics

```python
from app.services.security_metrics_engine import SecurityMetrics

# Create historical metrics (30 days)
historical_metrics = []
for i in range(30):
    historical_metrics.append(
        SecurityMetrics(
            total_findings=10 - i // 10,
            critical_count=max(0, 3 - i // 10),
            high_count=4,
            medium_count=2,
            low_count=1,
            findings_per_1000_loc=1.0,
            new_findings_last_24h=1,
            fixed_findings_last_24h=2,
            false_positive_rate=0.05,
            mean_time_to_detect=2.0,
            mean_time_to_fix=20.0,
            overall_risk_score=70.0 - i * 2,
            security_debt_score=50.0,
            trend_direction='IMPROVING',
            findings_per_developer={},
            fix_rate_per_developer={}
        )
    )

# Predict future risk
prediction = engine.predict_future_risk(historical_metrics, days_ahead=30)
print(f"Predicted Risk: {prediction['predicted_risk']}/100")
print(f"Confidence: {prediction['confidence']}%")
print(f"Trend: {prediction['trend']}")
```

### Anomaly Detection

```python
# Current metrics
current = SecurityMetrics(
    total_findings=50,
    critical_count=30,
    high_count=10,
    medium_count=5,
    low_count=5,
    findings_per_1000_loc=1.0,
    new_findings_last_24h=45,
    fixed_findings_last_24h=0,
    false_positive_rate=0.1,
    mean_time_to_detect=1.0,
    mean_time_to_fix=100.0,
    overall_risk_score=95.0,
    security_debt_score=90.0,
    trend_direction='DEGRADING',
    findings_per_developer={},
    fix_rate_per_developer={}
)

# Detect anomalies
anomalies = engine.detect_anomalies(
    current,
    historical_metrics,
    threshold_std=2.0
)

for anomaly in anomalies:
    print(f"Anomaly: {anomaly['metric']}")
    print(f"  Current: {anomaly['current_value']}")
    print(f"  Expected: {anomaly['expected_value']}")
    print(f"  Z-Score: {anomaly['z_score']}")
    print(f"  Severity: {anomaly['severity']}")
```

### Developer Performance Tracking

```python
# Calculate developer security score
dev_score = engine.calculate_developer_security_score(
    findings,
    developer_id="dev_001"
)

print(f"Developer: {dev_score['developer_id']}")
print(f"Security Score: {dev_score['security_score']}/100")
print(f"Grade: {dev_score['grade']}")
print(f"Findings Introduced: {dev_score['findings_introduced']}")
print(f"Findings Fixed: {dev_score['findings_fixed']}")
print(f"Fix Rate: {dev_score['fix_rate']}%")
```

### Security Debt Analysis

```python
# Calculate security debt
debt = engine.calculate_security_debt(
    findings,
    hourly_rate=100.0
)

print(f"Total Security Debt: ${debt['total_debt_usd']}")
print(f"Estimated Fix Time: {debt['estimated_fix_time_hours']} hours")
print(f"Debt by Severity:")
for severity, amount in debt['debt_by_severity'].items():
    print(f"  {severity}: ${amount}")
```

### Trend Analysis

```python
# Analyze security trends
trends = engine.analyze_trends(
    historical_metrics,
    window_days=30
)

print(f"Current Risk: {trends['current_risk']}/100")
print(f"7-Day MA: {trends['ma_7_days']}")
print(f"30-Day MA: {trends['ma_30_days']}")
print(f"Velocity: {trends['velocity']}")
print(f"Volatility: {trends['volatility']}")
print(f"Trend: {trends['trend']}")
```

## 📈 Algorithm Details

### 1. Advanced Risk Scoring Formula

```
Risk = Σ(Severity × Age × Exposure × CWE_multiplier) / Normalization_factor

Where:
- Severity: Weight based on finding severity (CRITICAL=10, HIGH=7.5, etc.)
- Age: 1 + (days_old / 30), capped at 5x
- Exposure: Based on file path (api/auth/admin = 1.5x, tests = 0.5x)
- CWE_multiplier: Risk multiplier for specific CWE types
- Normalization_factor: Scales to 0-100 range
```

### 2. Linear Regression (Predictive Analytics)

```
Future_Risk = slope × future_x + intercept

Where:
- slope = Σ((x - x_mean) × (y - y_mean)) / Σ((x - x_mean)²)
- intercept = y_mean - slope × x_mean
- Confidence = R² × 100
```

### 3. Z-Score Anomaly Detection

```
Z = (current_value - mean) / std_dev

Anomaly if |Z| > threshold (default: 2.0)
```

### 4. Developer Security Score

```
Score = 100 - Σ(severity_weights × unfixed_findings) + time_bonus

Grades:
- A+: 90-100
- A:  80-89
- B:  70-79
- C:  60-69
- F:  0-59
```

### 5. Security Debt

```
Debt = Σ(fix_time × hourly_rate × age_multiplier)

Where:
- fix_time: Estimated hours based on severity
- age_multiplier: 1 + (days_old / 365)
```

## 🎨 CWE Risk Multipliers

The engine includes special multipliers for common security vulnerabilities:

| CWE ID | Vulnerability Type | Multiplier |
|--------|-------------------|------------|
| CWE-89 | SQL Injection | 2.0x |
| CWE-79 | Cross-Site Scripting (XSS) | 1.8x |
| CWE-798 | Hard-coded Credentials | 2.5x |
| CWE-327 | Broken Cryptography | 1.5x |
| CWE-22 | Path Traversal | 1.7x |

## 🔍 Exposure Factor Patterns

### High Exposure (1.5x multiplier)
- `api/` - API endpoints
- `routes/` - Route handlers
- `views/` - View controllers
- `controllers/` - Controllers
- `auth/` - Authentication
- `login` - Login functionality
- `admin/` - Admin interfaces

### Low Exposure (0.5x multiplier)
- `test_` - Test files
- `tests/` - Test directories
- `migrations/` - Database migrations
- `scripts/` - Utility scripts

## 🧪 Testing

The engine includes 29 comprehensive tests covering:

- Data model creation and validation
- All 6 algorithms with edge cases
- Integration workflows
- Anomaly detection with various scenarios
- Developer scoring with different grades
- Security debt calculations
- Trend analysis with historical data

Run tests:
```bash
pytest tests/test_security_metrics_engine.py -v
```

## 📊 Example Report Output

```json
{
  "timestamp": "2025-11-01T18:24:23.884014",
  "summary": {
    "total_findings": 2,
    "open_findings": 1,
    "fixed_findings": 1,
    "false_positives": 0
  },
  "severity_distribution": {
    "CRITICAL": 1
  },
  "risk_analysis": {
    "overall_risk_score": 100.0,
    "risk_level": "CRITICAL"
  },
  "security_debt": {
    "total_debt_usd": 832.88,
    "debt_by_severity": {
      "CRITICAL": 832.88
    },
    "estimated_fix_time_hours": 8.0,
    "findings_count": 1
  },
  "performance_metrics": {
    "mean_time_to_fix_hours": 24.0,
    "median_time_to_fix_hours": 24.0,
    "fastest_fix_hours": 24.0,
    "slowest_fix_hours": 24.0
  },
  "developer_scores": {
    "dev_001": {
      "developer_id": "dev_001",
      "security_score": 90.0,
      "grade": "A+",
      "findings_introduced": 1,
      "findings_fixed": 0,
      "avg_fix_time_hours": 0,
      "fix_rate": 0.0
    },
    "dev_002": {
      "developer_id": "dev_002",
      "security_score": 100,
      "grade": "A+",
      "findings_introduced": 0,
      "findings_fixed": 1,
      "avg_fix_time_hours": 24.0,
      "fix_rate": 100.0
    }
  },
  "recommendations": [
    "🚨 URGENT: Fix 1 critical security issues immediately",
    "📊 Overall risk score is high - consider security sprint",
    "💉 Found 1 SQL injection risks - prioritize immediately"
  ]
}
```

## 🌟 Best Practices

1. **Regular Monitoring**: Run analysis daily or after each commit
2. **Historical Tracking**: Maintain at least 30 days of metrics for trends
3. **Threshold Tuning**: Adjust anomaly detection threshold based on team size and activity
4. **Developer Engagement**: Use gamification scores to encourage security awareness
5. **Debt Management**: Track security debt alongside technical debt
6. **Prioritization**: Focus on CRITICAL and HIGH severity findings first
7. **False Positive Management**: Mark false positives to improve accuracy

## 🔧 Configuration

### Severity Weights (CVSS-inspired)
```python
severity_weights = {
    'CRITICAL': 10.0,
    'HIGH': 7.5,
    'MEDIUM': 5.0,
    'LOW': 2.5,
    'INFO': 1.0
}
```

### Fix Time Estimates (hours)
```python
fix_time_estimates = {
    'CRITICAL': 8.0,
    'HIGH': 4.0,
    'MEDIUM': 2.0,
    'LOW': 1.0,
    'INFO': 0.5
}
```

## 🚀 Advanced Use Cases

### 1. CI/CD Integration
Integrate into your CI/CD pipeline to track security over time:
```bash
python -m app.services.security_metrics_engine > security_report.json
```

### 2. Dashboard Visualization
Feed the JSON output to visualization tools like Grafana or custom dashboards.

### 3. Slack/Email Alerts
Set up alerts when anomalies are detected or risk scores exceed thresholds.

### 4. Team Leaderboards
Use developer scores to create friendly competition and security awareness.

### 5. Sprint Planning
Use security debt calculations to plan security-focused sprints.

## 📚 References

This implementation is inspired by:
- Google's Security Command Center
- Meta's Security Platform
- AWS GuardDuty ML
- DataDog Anomaly Detection
- SonarQube Technical Debt
- GitHub Advanced Security

## 🤝 Contributing

To extend the engine:
1. Add new CWE multipliers in `cwe_risk_multipliers`
2. Add new exposure patterns in `_calculate_exposure_factor`
3. Create new recommendation rules in `_generate_recommendations`
4. Add tests for new functionality

## 📝 License

Part of the CogniForge project.

---

**Built with ❤️ to make security measurable and actionable**
