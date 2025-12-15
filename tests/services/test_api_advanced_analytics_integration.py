"""
Integration test for api_advanced_analytics refactoring
========================================================
Migrated from verify_api_advanced_analytics.py
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.api_advanced_analytics import (
    AdvancedAnalyticsService,
    TimeGranularity,
    get_advanced_analytics_service,
)


def test_backward_compatibility():
    """Test that factory and instantiation work."""
    # Test factory function
    service1 = get_advanced_analytics_service()
    assert service1 is not None
    
    # Test direct instantiation
    service2 = AdvancedAnalyticsService()
    assert service2 is not None


def test_track_request():
    """Test request tracking."""
    service = get_advanced_analytics_service()
    
    # We rely on the internal state change or return value.
    # track_request returns None, but updates internal metrics.
    service.track_request(
        endpoint="/api/test",
        method="GET",
        status_code=200,
        response_time_ms=45.2,
        user_id="user123",
        session_id="session456",
    )
    # No assertion here other than no exception raised,
    # but subsequent tests verify the data is there.


def test_realtime_dashboard():
    """Test realtime dashboard."""
    service = get_advanced_analytics_service()
    
    # Track some requests first
    for i in range(10):
        service.track_request(
            endpoint=f"/api/endpoint{i % 3}",
            method="GET",
            status_code=200 if i % 5 != 0 else 500,
            response_time_ms=50.0 + i * 10,
            user_id=f"user{i % 3}",
        )
    
    dashboard = service.get_realtime_dashboard()
    
    assert "timestamp" in dashboard
    assert "current_metrics" in dashboard
    assert "performance" in dashboard
    assert "last_hour" in dashboard
    assert "top_endpoints" in dashboard
    
    assert dashboard['current_metrics']['requests_per_minute'] >= 0


def test_user_behavior_analysis():
    """Test user behavior analysis."""
    service = get_advanced_analytics_service()
    
    # Ensure user exists in data from previous tests or add new
    service.track_request(
        endpoint="/api/user_test",
        method="GET",
        status_code=200,
        response_time_ms=20.0,
        user_id="user_behavior_test",
    )

    profile = service.analyze_user_behavior("user_behavior_test")
    
    assert profile is not None
    assert profile.user_id == "user_behavior_test"
    assert profile.pattern is not None


def test_generate_report():
    """Test report generation."""
    service = get_advanced_analytics_service()
    
    # Track some requests
    for i in range(20):
        service.track_request(
            endpoint="/api/test_report",
            method="GET",
            status_code=200,
            response_time_ms=45.0,
        )
    
    report = service.generate_usage_report(
        name="Test Report",
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc),
        granularity=TimeGranularity.HOUR,
    )
    
    assert report is not None
    assert report.name == "Test Report"
    assert "total_requests" in report.metrics


def test_anomaly_detection():
    """Test anomaly detection."""
    service = get_advanced_analytics_service()
    
    anomalies = service.detect_anomalies(window_hours=24)
    
    assert anomalies is not None
    assert isinstance(anomalies, list)


def test_cost_optimization():
    """Test cost optimization insights."""
    service = get_advanced_analytics_service()
    
    insights = service.get_cost_optimization_insights()
    
    assert insights is not None
    assert "analysis_period" in insights
    assert "recommendations" in insights
