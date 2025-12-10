"""API layer - Facade and entry points."""

from app.security_metrics.api.security_metrics_facade import SecurityMetricsFacade, get_security_metrics_facade

__all__ = ["SecurityMetricsFacade", "get_security_metrics_facade"]
