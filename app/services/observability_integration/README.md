# Observability Integration Service

## Overview

Hexagonal architecture implementation for observability and monitoring integration.

## Architecture

```
observability_integration/
├── domain/              # Pure business logic
│   ├── models.py       # Entities (Metric, Span, Alert, etc.)
│   └── ports.py        # Interfaces (IMetricsCollector, ITraceExporter, etc.)
├── application/        # Use cases
│   ├── metrics_manager.py
│   ├── trace_manager.py
│   ├── alert_manager.py
│   ├── health_monitor.py
│   └── performance_tracker.py
├── infrastructure/     # Adapters
│   └── in_memory_repositories.py
└── facade.py          # Unified interface
```

## Features

- **Metrics Collection**: Prometheus-style metrics (Counter, Gauge, Histogram, Summary)
- **Distributed Tracing**: W3C Trace Context compatible
- **Alerting**: Multi-severity alert system
- **Health Monitoring**: Component health tracking
- **Performance Tracking**: System performance snapshots

## Usage

```python
from app.services.observability_integration import ObservabilityIntegrationFacade

# Initialize
service = ObservabilityIntegrationFacade()

# Record metrics
service.record_metric("api.requests", 100, MetricType.COUNTER)

# Start tracing
span = service.start_span("process_request")
service.add_span_tag(span, "user_id", "123")
service.finish_span(span, TraceStatus.OK)

# Trigger alerts
service.trigger_alert(
    "high_error_rate",
    AlertSeverity.WARNING,
    "Error rate exceeded threshold",
    "api_gateway"
)

# Check health
health = service.get_overall_health()
```

## Migration

Original file: `observability_integration_service.py` (592 lines)
New structure: ~60 lines (shim) + modular architecture

**Reduction**: 90% in main file
**Breaking Changes**: None
**Backward Compatibility**: 100%
