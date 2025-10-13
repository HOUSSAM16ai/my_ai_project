# app/api/analytics_routes.py
# ======================================================================================
# ==    SUPERHUMAN ANALYTICS API ROUTES (v1.0)                                     ==
# ======================================================================================

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request

from app.middleware.decorators import monitor_performance, rate_limit, require_jwt_auth
from app.services.api_advanced_analytics_service import (
    BehaviorPattern,
    TimeGranularity,
    get_advanced_analytics_service,
)

# Create blueprint
api_bp = Blueprint("analytics_api", __name__, url_prefix="/api")


# ======================================================================================
# REAL-TIME ANALYTICS
# ======================================================================================


@api_bp.route("/analytics/dashboard/realtime", methods=["GET"])
@rate_limit
@monitor_performance
def get_realtime_dashboard():
    """
    Get real-time analytics dashboard

    Returns:
    - Current requests per minute
    - Active users
    - Error rate
    - Performance metrics (P50, P95, P99)
    - Top endpoints
    """
    try:
        service = get_advanced_analytics_service()
        dashboard = service.get_realtime_dashboard()

        return jsonify({"status": "success", "data": dashboard}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting realtime dashboard: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve realtime dashboard"}), 500


# ======================================================================================
# USAGE REPORTS
# ======================================================================================


@api_bp.route("/analytics/reports/usage", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def generate_usage_report():
    """
    Generate comprehensive usage report

    Query Parameters:
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - granularity: Time granularity (minute, hour, day, week, month)
    """
    try:
        # Parse dates
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if not start_date_str or not end_date_str:
            # Default to last 7 days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))

        # Parse granularity
        granularity_str = request.args.get("granularity", "day").upper()
        try:
            granularity = TimeGranularity[granularity_str]
        except KeyError:
            granularity = TimeGranularity.DAY

        service = get_advanced_analytics_service()
        report = service.generate_usage_report(start_date, end_date, granularity)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "report_id": report.report_id,
                        "name": report.name,
                        "generated_at": report.generated_at.isoformat(),
                        "time_range": {
                            "start": report.time_range[0].isoformat(),
                            "end": report.time_range[1].isoformat(),
                        },
                        "granularity": report.granularity.value,
                        "metrics": report.metrics,
                        "insights": report.insights,
                        "recommendations": report.recommendations,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating usage report: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to generate usage report"}), 500


# ======================================================================================
# BEHAVIOR ANALYTICS
# ======================================================================================


@api_bp.route("/analytics/behavior/<user_id>", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def analyze_user_behavior(user_id: str):
    """
    Analyze user behavior and create profile

    Returns:
    - Behavior pattern classification
    - Usage statistics
    - Favorite endpoints
    - Peak usage hours
    - Churn probability
    - Lifetime value estimate
    """
    try:
        service = get_advanced_analytics_service()
        profile = service.analyze_user_behavior(user_id)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "user_id": profile.user_id,
                        "pattern": profile.pattern.value,
                        "statistics": {
                            "avg_requests_per_day": round(profile.avg_requests_per_day, 2),
                            "avg_session_duration": round(profile.avg_session_duration, 2),
                            "favorite_endpoints": profile.favorite_endpoints,
                            "peak_usage_hours": profile.peak_usage_hours,
                        },
                        "predictions": {
                            "churn_probability": round(profile.churn_probability, 2),
                            "lifetime_value_estimate": round(profile.lifetime_value_estimate, 2),
                        },
                        "last_updated": profile.last_updated.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error analyzing user behavior: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to analyze user behavior"}), 500


# ======================================================================================
# ANOMALY DETECTION
# ======================================================================================


@api_bp.route("/analytics/anomalies", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def detect_anomalies():
    """
    Detect anomalies in API usage

    Query Parameters:
    - window_hours: Time window for analysis (default: 24)

    Returns:
    - Traffic spikes
    - High error rates
    - Unusual patterns
    """
    try:
        window_hours = int(request.args.get("window_hours", 24))

        service = get_advanced_analytics_service()
        anomalies = service.detect_anomalies(window_hours=window_hours)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "anomalies": anomalies,
                        "total": len(anomalies),
                        "window_hours": window_hours,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to detect anomalies"}), 500


# ======================================================================================
# COST OPTIMIZATION
# ======================================================================================


@api_bp.route("/analytics/cost-optimization", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_cost_optimization_insights():
    """
    Get cost optimization insights

    Returns:
    - Inefficient endpoints
    - Optimization recommendations
    - Cost-saving opportunities
    """
    try:
        service = get_advanced_analytics_service()
        insights = service.get_cost_optimization_insights()

        return jsonify({"status": "success", "data": insights}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting cost optimization insights: {str(e)}")
        return (
            jsonify(
                {"status": "error", "message": "Failed to retrieve cost optimization insights"}
            ),
            500,
        )


# ======================================================================================
# USER JOURNEYS
# ======================================================================================


@api_bp.route("/analytics/journeys/<user_id>", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_user_journeys(user_id: str):
    """
    Get user journeys

    Query Parameters:
    - session_id: Filter by specific session (optional)
    """
    try:
        service = get_advanced_analytics_service()
        session_id = request.args.get("session_id")

        # Get user journeys
        journeys = []
        for journey_key, journey in service.user_journeys.items():
            if journey.user_id != user_id:
                continue
            if session_id and journey.session_id != session_id:
                continue

            journeys.append(
                {
                    "user_id": journey.user_id,
                    "session_id": journey.session_id,
                    "start_time": journey.start_time.isoformat(),
                    "end_time": journey.end_time.isoformat() if journey.end_time else None,
                    "total_requests": journey.total_requests,
                    "unique_endpoints": journey.unique_endpoints,
                    "total_duration_seconds": journey.total_duration_seconds,
                    "completed_actions": journey.completed_actions,
                    "errors_encountered": journey.errors_encountered,
                    "events_count": len(journey.events),
                }
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"user_id": user_id, "journeys": journeys, "total": len(journeys)},
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting user journeys: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve user journeys"}), 500


# ======================================================================================
# METRICS TRACKING
# ======================================================================================


@api_bp.route("/analytics/track", methods=["POST"])
@rate_limit
@monitor_performance
def track_request_metrics():
    """
    Track API request metrics (internal use)

    Request Body:
    {
        "endpoint": "/api/users",
        "method": "GET",
        "status_code": 200,
        "response_time_ms": 45.2,
        "user_id": "user_123",
        "session_id": "sess_456",
        "metadata": {}
    }
    """
    try:
        data = request.get_json()

        required_fields = ["endpoint", "method", "status_code", "response_time_ms"]
        if not data or not all(field in data for field in required_fields):
            return (
                jsonify(
                    {"status": "error", "message": f'Required fields: {", ".join(required_fields)}'}
                ),
                400,
            )

        service = get_advanced_analytics_service()
        service.track_request(
            endpoint=data["endpoint"],
            method=data["method"],
            status_code=data["status_code"],
            response_time_ms=data["response_time_ms"],
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            metadata=data.get("metadata"),
        )

        return jsonify({"status": "success", "message": "Metrics tracked successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error tracking metrics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to track metrics"}), 500


# ======================================================================================
# PERFORMANCE INSIGHTS
# ======================================================================================


@api_bp.route("/analytics/performance/insights", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_performance_insights():
    """
    Get performance insights

    Query Parameters:
    - hours: Time window in hours (default: 24)
    """
    try:
        hours = int(request.args.get("hours", 24))

        service = get_advanced_analytics_service()
        dashboard = service.get_realtime_dashboard()

        # Get insights from dashboard and cost optimization
        cost_insights = service.get_cost_optimization_insights()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "time_window_hours": hours,
                        "performance": dashboard.get("performance", {}),
                        "current_metrics": dashboard.get("current_metrics", {}),
                        "inefficient_endpoints": cost_insights.get("inefficient_endpoints", []),
                        "recommendations": cost_insights.get("recommendations", []),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting performance insights: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve performance insights"}),
            500,
        )
