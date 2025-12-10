"""API layer - Facade and entry points."""

from app.analytics.api.analytics_facade import AnalyticsFacade, get_analytics_facade

__all__ = ["AnalyticsFacade", "get_analytics_facade"]
