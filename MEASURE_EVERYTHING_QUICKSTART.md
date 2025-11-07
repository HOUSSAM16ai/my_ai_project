# 📊 Measure Everything System - Quick Start Guide

## 🚀 Quick Start

### Installation
```bash
# Install required dependency
pip install psutil>=5.9.0
```

### Basic Usage

#### 1. Infrastructure Metrics
```python
from app.services.infrastructure_metrics_service import get_infrastructure_service

# Get service instance
infra = get_infrastructure_service()

# Collect metrics
cpu = infra.collect_cpu_metrics()
memory = infra.collect_memory_metrics()
disk = infra.collect_disk_metrics()
network = infra.collect_network_metrics()

# Get summary
summary = infra.get_metrics_summary()
print(f"CPU: {summary['cpu']['current_percent']}%")
print(f"Memory: {summary['memory']['used_percent']}%")
```

#### 2. AI Model Metrics
```python
from app.services.ai_model_metrics_service import get_ai_model_service, ModelType

# Get service instance
ai = get_ai_model_service()

# Register model
ai.register_model("gpt-4", "1.0", ModelType.NLP_GENERATION)

# Record inference
ai.record_inference(
    model_name="gpt-4",
    model_version="1.0",
    latency_ms=150.5,
    input_tokens=100,
    output_tokens=200,
    cost_usd=0.005
)

# Get latency metrics
latency = ai.get_latency_metrics("gpt-4", "1.0")
print(f"P95 Latency: {latency.p95_ms}ms")
```

#### 3. User Analytics
```python
from app.services.user_analytics_metrics_service import get_user_analytics_service, EventType

# Get service instance
analytics = get_user_analytics_service()

# Track event
analytics.track_event(
    user_id=123,
    event_type=EventType.PAGE_VIEW,
    event_name="home_page",
    page_url="/home"
)

# Get engagement metrics
engagement = analytics.get_engagement_metrics()
print(f"DAU: {engagement.dau}, MAU: {engagement.mau}")
```

## 🌐 API Endpoints

### Infrastructure Metrics
```bash
# Get summary
curl http://localhost:5000/api/v1/metrics/infrastructure/summary

# Get CPU metrics
curl http://localhost:5000/api/v1/metrics/infrastructure/cpu

# Get memory metrics
curl http://localhost:5000/api/v1/metrics/infrastructure/memory

# Prometheus export
curl http://localhost:5000/api/v1/metrics/infrastructure/prometheus
```

### AI Model Metrics
```bash
# Get all models
curl http://localhost:5000/api/v1/metrics/ai/models

# Get specific model
curl http://localhost:5000/api/v1/metrics/ai/models/gpt-4/1.0

# Register model
curl -X POST http://localhost:5000/api/v1/metrics/ai/models/register \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-4",
    "model_version": "1.0",
    "model_type": "nlp_generation"
  }'

# Record inference
curl -X POST http://localhost:5000/api/v1/metrics/ai/inferences/record \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-4",
    "model_version": "1.0",
    "latency_ms": 150.5,
    "input_tokens": 100,
    "output_tokens": 200,
    "cost_usd": 0.005
  }'
```

### User Analytics
```bash
# Get summary
curl http://localhost:5000/api/v1/metrics/users/summary

# Get engagement metrics
curl http://localhost:5000/api/v1/metrics/users/engagement

# Get conversion metrics
curl http://localhost:5000/api/v1/metrics/users/conversion

# Get NPS metrics
curl http://localhost:5000/api/v1/metrics/users/nps

# Track event
curl -X POST http://localhost:5000/api/v1/metrics/users/events/track \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "event_type": "page_view",
    "event_name": "home_page",
    "page_url": "/home"
  }'
```

### Unified Dashboard
```bash
# Get unified dashboard with all metrics
curl http://localhost:5000/api/v1/metrics/dashboard
```

## 📊 Key Metrics

### Infrastructure KPIs
- **CPU Usage**: Target < 80%
- **Memory Usage**: Target < 80%
- **Disk Usage**: Target < 80%
- **Network Throughput**: Real-time monitoring
- **Availability**: Target > 99.9%

### AI Model KPIs
- **Inference Latency P95**: Target < 200ms
- **Cost Per Request**: Target < $0.01
- **Model Accuracy**: Target > 95%
- **Model Drift Score**: Target < 0.1
- **Health Score**: Target > 90

### User Experience KPIs
- **DAU/MAU Ratio**: Target > 0.2
- **Conversion Rate**: Target > 5%
- **Day 7 Retention**: Target > 40%
- **NPS Score**: Target > 40
- **Bounce Rate**: Target < 40%

## 🎯 Common Use Cases

### 1. Monitor System Health
```python
infra = get_infrastructure_service()
summary = infra.get_metrics_summary()

if summary['status'] == 'critical':
    print("⚠️ System in critical state!")
    print(f"CPU: {summary['cpu']['current_percent']}%")
    print(f"Memory: {summary['memory']['used_percent']}%")
```

### 2. Track Model Performance
```python
ai = get_ai_model_service()
snapshot = ai.get_model_performance_snapshot("gpt-4", "1.0")

print(f"Health Score: {snapshot.health_score}/100")
print("Recommendations:")
for rec in snapshot.recommendations:
    print(f"  - {rec}")
```

### 3. Analyze User Behavior
```python
analytics = get_user_analytics_service()

# Get engagement
engagement = analytics.get_engagement_metrics()
print(f"Daily Active Users: {engagement.dau}")

# Get conversion
conversion = analytics.get_conversion_metrics()
print(f"Conversion Rate: {conversion.conversion_rate * 100}%")

# Get retention
retention = analytics.get_retention_metrics()
print(f"Day 7 Retention: {retention.day_7_retention * 100}%")
```

### 4. Detect Model Drift
```python
ai = get_ai_model_service()
drift = ai.detect_model_drift("gpt-4", "1.0")

if drift and drift.drift_status != DriftStatus.NO_DRIFT:
    print(f"⚠️ Model drift detected: {drift.drift_status.value}")
    print(f"Drift Score: {drift.drift_score}")
    print("Recommendation: Retrain model with recent data")
```

### 5. Run A/B Test
```python
analytics = get_user_analytics_service()

# Create test
test_id = analytics.create_ab_test(
    test_name="New Homepage",
    variants=["control", "variant_a"]
)

# Assign users
for user_id in [1, 2, 3, 4, 5]:
    variant = analytics.assign_variant(test_id, user_id)
    print(f"User {user_id} assigned to {variant}")

# Record conversions
analytics.record_ab_conversion(test_id, user_id=1)

# Get results
results = analytics.get_ab_test_results(test_id)
print(f"Control Rate: {results.control_conversion_rate}")
print(f"Variant A Rate: {results.variant_conversion_rates['variant_a']}")
```

## 🔧 Configuration

### Start Background Collection
```python
from app.services.infrastructure_metrics_service import get_infrastructure_service

# Start automatic metrics collection every 10 seconds
service = get_infrastructure_service()
service.start_background_collection()
```

### Register Services for Availability Tracking
```python
# Register a service with 99.9% SLA target
service.register_service("my-api", sla_target=99.9)

# Record downtime
service.record_service_down("my-api")

# Record recovery
service.record_service_up("my-api")

# Check availability
availability = service.get_availability_metrics("my-api")
print(f"Availability: {availability.availability_percent}%")
print(f"SLA Compliance: {availability.sla_compliance}")
```

## 📈 Prometheus Integration

### Export Metrics for Prometheus
```bash
curl http://localhost:5000/api/v1/metrics/infrastructure/prometheus
```

### Configure Prometheus
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'cogniforge'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/api/v1/metrics/infrastructure/prometheus'
    scrape_interval: 30s
```

## 🎨 Dashboard Integration

### Response Format
All endpoints return JSON in this format:
```json
{
  "status": "success",
  "data": {
    ...metrics...
  }
}
```

### Error Handling
```json
{
  "status": "error",
  "message": "Error description"
}
```

## 🚨 Alerting Rules (Recommendations)

### Infrastructure Alerts
- CPU > 90% for 5 minutes
- Memory > 90% for 5 minutes
- Disk > 90%
- Availability < 99.9%

### AI Model Alerts
- P95 Latency > 500ms
- Cost per request > $0.05
- Drift score > 0.3
- Health score < 80

### User Experience Alerts
- DAU drops by > 20%
- Conversion rate drops by > 30%
- NPS score < 0

## 📚 Additional Resources

- Full documentation: `MEASURE_EVERYTHING_SYSTEM_AR.md`
- Infrastructure service: `app/services/infrastructure_metrics_service.py`
- AI model service: `app/services/ai_model_metrics_service.py`
- User analytics service: `app/services/user_analytics_metrics_service.py`
- API routes: `app/api/comprehensive_metrics_routes.py`

## 🏆 Features Comparison

| Feature | Status | Description |
|---------|--------|-------------|
| Infrastructure Metrics | ✅ | CPU, Memory, Disk, Network |
| AI Model Metrics | ✅ | Latency, Cost, Accuracy, Drift |
| User Analytics | ✅ | DAU/MAU, Conversion, Retention |
| A/B Testing | ✅ | Built-in framework |
| NPS Tracking | ✅ | Net Promoter Score |
| Prometheus Export | ✅ | Standard format |
| Real-time Monitoring | ✅ | Background collection |
| Unified Dashboard | ✅ | All metrics in one place |

---

**Built with ❤️ by Houssam Benmerah**

A world-class monitoring system surpassing tech giants! 🚀
