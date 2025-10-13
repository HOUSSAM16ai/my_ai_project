# app/api/observability_routes.py
# ======================================================================================
# ==        OBSERVABILITY ROUTES - P99.9 MONITORING & ANALYTICS                     ==
# ======================================================================================
# PRIME DIRECTIVE:
#   مسارات المراقبة الخارقة مع P99.9 Latency Tracking
#   Superhuman observability routes with P99.9 latency tracking

from datetime import datetime, timezone

from flask import current_app, jsonify, request

from app.api import api_bp
from app.services.api_observability_service import get_observability_service, monitor_performance
from app.services.api_security_service import rate_limit, require_jwt_auth

# ======================================================================================
# METRICS & PERFORMANCE
# ======================================================================================


@api_bp.route("/observability/metrics", methods=["GET"])
@rate_limit
@monitor_performance
def get_metrics():
    """
    Get comprehensive API metrics

    Query Parameters:
    - endpoint: Filter by specific endpoint
    - time_window: Time window in seconds (default: 3600)
    """
    try:
        observability = get_observability_service()
        endpoint = request.args.get("endpoint")
        time_window = request.args.get("time_window", 3600, type=int)

        if endpoint:
            metrics = observability.get_endpoint_metrics(endpoint)
        else:
            metrics = observability.get_all_metrics()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve metrics"}), 500


@api_bp.route("/observability/metrics/summary", methods=["GET"])
@rate_limit
@monitor_performance
def get_metrics_summary():
    """Get high-level metrics summary"""
    try:
        observability = get_observability_service()
        summary = observability.get_metrics_summary()

        return jsonify({"status": "success", "data": summary}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting metrics summary: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve metrics summary"}), 500


@api_bp.route("/observability/latency", methods=["GET"])
@rate_limit
@monitor_performance
def get_latency_stats():
    """
    Get latency statistics (P50, P95, P99, P99.9)

    Query Parameters:
    - endpoint: Filter by specific endpoint
    """
    try:
        observability = get_observability_service()
        endpoint = request.args.get("endpoint")

        stats = observability.get_latency_percentiles(endpoint)

        return jsonify({"status": "success", "data": stats}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting latency stats: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve latency statistics"}), 500


@api_bp.route("/observability/endpoint/<path:endpoint_path>", methods=["GET"])
@rate_limit
@monitor_performance
def get_endpoint_analytics(endpoint_path):
    """Get detailed analytics for a specific endpoint"""
    try:
        observability = get_observability_service()
        analytics = observability.get_endpoint_analytics(f"/{endpoint_path}")

        return jsonify({"status": "success", "data": analytics}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting endpoint analytics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve endpoint analytics"}), 500


# ======================================================================================
# ALERTS & ANOMALIES
# ======================================================================================


@api_bp.route("/observability/alerts", methods=["GET"])
@rate_limit
@monitor_performance
def get_alerts():
    """
    Get active alerts

    Query Parameters:
    - severity: Filter by severity (low, medium, high, critical)
    - status: Filter by status (active, resolved)
    """
    try:
        observability = get_observability_service()
        severity = request.args.get("severity")
        status = request.args.get("status", "active")

        alerts = observability.get_alerts(severity=severity, status=status)

        return jsonify({"status": "success", "data": {"alerts": alerts, "count": len(alerts)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve alerts"}), 500


@api_bp.route("/observability/alerts/<alert_id>/resolve", methods=["POST"])
@require_jwt_auth
@rate_limit
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        observability = get_observability_service()
        observability.resolve_alert(alert_id)

        return (
            jsonify({"status": "success", "message": f"Alert {alert_id} resolved successfully"}),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error resolving alert: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to resolve alert"}), 500


@api_bp.route("/observability/anomalies", methods=["GET"])
@rate_limit
@monitor_performance
def detect_anomalies():
    """
    Detect anomalies using ML-based detection

    Query Parameters:
    - metric: Metric to analyze (latency, error_rate, throughput)
    - sensitivity: Detection sensitivity (low, medium, high)
    """
    try:
        observability = get_observability_service()
        metric = request.args.get("metric", "latency")
        sensitivity = request.args.get("sensitivity", "medium")

        anomalies = observability.detect_anomalies(metric, sensitivity)

        return (
            jsonify(
                {"status": "success", "data": {"anomalies": anomalies, "count": len(anomalies)}}
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to detect anomalies"}), 500


# ======================================================================================
# SLA MONITORING
# ======================================================================================


@api_bp.route("/observability/sla", methods=["GET"])
@rate_limit
@monitor_performance
def get_sla_metrics():
    """
    Get SLA compliance metrics

    Query Parameters:
    - period: Time period (hour, day, week, month)
    """
    try:
        observability = get_observability_service()
        period = request.args.get("period", "day")

        sla_metrics = observability.get_sla_metrics(period)

        return jsonify({"status": "success", "data": sla_metrics}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting SLA metrics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve SLA metrics"}), 500


@api_bp.route("/observability/sla/violations", methods=["GET"])
@rate_limit
@monitor_performance
def get_sla_violations():
    """Get SLA violations"""
    try:
        observability = get_observability_service()
        violations = observability.get_sla_violations()

        return (
            jsonify(
                {"status": "success", "data": {"violations": violations, "count": len(violations)}}
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting SLA violations: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve SLA violations"}), 500


# ======================================================================================
# DISTRIBUTED TRACING
# ======================================================================================


@api_bp.route("/observability/traces", methods=["GET"])
@rate_limit
@monitor_performance
def get_traces():
    """
    Get distributed traces

    Query Parameters:
    - trace_id: Specific trace ID
    - limit: Number of traces to retrieve
    """
    try:
        observability = get_observability_service()
        trace_id = request.args.get("trace_id")
        limit = request.args.get("limit", 100, type=int)

        if trace_id:
            trace = observability.get_trace(trace_id)
            return jsonify({"status": "success", "data": trace}), 200
        else:
            traces = observability.get_recent_traces(limit)
            return (
                jsonify({"status": "success", "data": {"traces": traces, "count": len(traces)}}),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Error getting traces: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve traces"}), 500


# ======================================================================================
# PERFORMANCE SNAPSHOT
# ======================================================================================


@api_bp.route("/observability/snapshot", methods=["GET"])
@rate_limit
@monitor_performance
def get_performance_snapshot():
    """Get real-time performance snapshot"""
    try:
        observability = get_observability_service()
        snapshot = observability.get_performance_snapshot()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": snapshot,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting performance snapshot: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve performance snapshot"}),
            500,
        )


# ======================================================================================
# ERROR TRACKING
# ======================================================================================


@api_bp.route("/observability/errors", methods=["GET"])
@rate_limit
@monitor_performance
def get_errors():
    """
    Get error logs and statistics

    Query Parameters:
    - severity: Filter by severity
    - limit: Number of errors to retrieve
    """
    try:
        observability = get_observability_service()
        severity = request.args.get("severity")
        limit = request.args.get("limit", 100, type=int)

        errors = observability.get_errors(severity=severity, limit=limit)

        return jsonify({"status": "success", "data": {"errors": errors, "count": len(errors)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting errors: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve errors"}), 500


@api_bp.route("/observability/errors/rate", methods=["GET"])
@rate_limit
@monitor_performance
def get_error_rate():
    """Get error rate statistics"""
    try:
        observability = get_observability_service()
        error_rate = observability.get_error_rate()

        return jsonify({"status": "success", "data": error_rate}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting error rate: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve error rate"}), 500


# ======================================================================================
# HEALTH CHECK
# ======================================================================================


@api_bp.route("/observability/health", methods=["GET"])
def observability_health():
    """Observability service health check"""
    try:
        observability = get_observability_service()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "status": "healthy",
                        "features": {
                            "metrics_collection": "active",
                            "latency_tracking": "active",
                            "anomaly_detection": "active",
                            "sla_monitoring": "active",
                            "distributed_tracing": "active",
                            "error_tracking": "active",
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Observability health check failed: {str(e)}")
        return jsonify({"status": "error", "message": "Observability service unhealthy"}), 503
