# app/api/unified_observability_routes.py
# ======================================================================================
# ==   UNIFIED OBSERVABILITY API ROUTES - COMPLETE MONITORING INTERFACE            ==
# ======================================================================================
"""
مسارات API للملاحظية الموحدة - Unified Observability API Routes

Provides comprehensive API for all observability data:
✅ Metrics (Golden Signals, RED, USE)
✅ Traces (distributed tracing, correlation)
✅ Logs (structured, correlated)
✅ Anomaly Detection
✅ Service Dependencies
✅ SLA/SLO Monitoring
✅ Performance Analysis

Better than:
- Prometheus API (more features, better correlation)
- Jaeger API (integrated metrics + logs)
- Grafana (programmatic access, ML anomalies)
"""

from datetime import UTC, datetime

from flask import current_app, jsonify, request

from app.api import api_bp
from app.telemetry.unified_observability import get_unified_observability


# ======================================================================================
# GOLDEN SIGNALS - GOOGLE SRE METHODOLOGY
# ======================================================================================
@api_bp.route("/observability/golden-signals", methods=["GET"])
def get_golden_signals():
    """
    Get Golden Signals (Google SRE)

    Query Parameters:
    - time_window: Time window in seconds (default: 300)

    Returns:
    - LATENCY: P50, P95, P99, P99.9
    - TRAFFIC: Requests per second
    - ERRORS: Error rate
    - SATURATION: Active requests, queue depth
    """
    try:
        time_window = request.args.get("time_window", 300, type=int)
        obs = get_unified_observability()

        signals = obs.get_golden_signals(time_window_seconds=time_window)

        return (
            jsonify(
                {"status": "success", "data": signals, "timestamp": datetime.now(UTC).isoformat()}
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting golden signals: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve golden signals"}), 500


# ======================================================================================
# DISTRIBUTED TRACING
# ======================================================================================
@api_bp.route("/observability/traces/<trace_id>", methods=["GET"])
def get_trace_details(trace_id: str):
    """
    Get complete trace with ALL correlated data

    This is the POWER of unified observability:
    - Trace with all spans
    - All logs for this trace_id
    - All metrics for this trace_id
    - Service dependencies
    - Critical path analysis

    Returns complete context in ONE request!
    """
    try:
        obs = get_unified_observability()
        trace_data = obs.get_trace_with_correlation(trace_id)

        if not trace_data:
            return jsonify({"status": "error", "message": "Trace not found"}), 404

        return jsonify({"status": "success", "data": trace_data}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting trace: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve trace"}), 500


@api_bp.route("/observability/traces/search", methods=["GET"])
def search_traces():
    """
    Search traces by criteria

    Query Parameters:
    - min_duration_ms: Minimum duration in milliseconds
    - has_errors: Filter by error status (true/false)
    - operation_name: Filter by operation name
    - limit: Maximum number of results (default: 100)
    """
    try:
        obs = get_unified_observability()

        min_duration = request.args.get("min_duration_ms", type=float)
        has_errors = request.args.get("has_errors", type=lambda v: v.lower() == "true")
        operation_name = request.args.get("operation_name")
        limit = request.args.get("limit", 100, type=int)

        traces = obs.find_traces_by_criteria(
            min_duration_ms=min_duration,
            has_errors=has_errors,
            operation_name=operation_name,
            limit=limit,
        )

        return jsonify({"status": "success", "data": {"traces": traces, "count": len(traces)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error searching traces: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to search traces"}), 500


@api_bp.route("/observability/traces/slow", methods=["GET"])
def get_slow_traces():
    """
    Get slow traces (exceeding SLA)

    Query Parameters:
    - threshold_ms: Duration threshold (default: 100ms)
    - limit: Maximum number of results (default: 50)
    """
    try:
        threshold = float(request.args.get("threshold_ms", "100"))
        limit = int(request.args.get("limit", "50"))

        obs = get_unified_observability()
        traces = obs.find_traces_by_criteria(min_duration_ms=threshold, limit=limit)

        return jsonify({"status": "success", "data": {"traces": traces, "count": len(traces)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting slow traces: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve slow traces"}), 500


# ======================================================================================
# METRICS & PERCENTILES
# ======================================================================================
@api_bp.route("/observability/metrics/percentiles", methods=["GET"])
def get_metric_percentiles():
    """
    Get percentiles for a specific metric

    Query Parameters:
    - metric: Metric name (default: http.request.duration_seconds)

    Returns P50, P90, P95, P99, P99.9
    """
    try:
        metric_name = request.args.get("metric", "http.request.duration_seconds")
        obs = get_unified_observability()

        percentiles = obs.get_percentiles(metric_name)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"metric": metric_name, "percentiles": percentiles},
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting percentiles: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve percentiles"}), 500


@api_bp.route("/observability/metrics/prometheus", methods=["GET"])
def export_prometheus_metrics():
    """
    Export metrics in Prometheus format

    Compatible with:
    - Prometheus scraping
    - Grafana data source
    - Victoria Metrics
    """
    try:
        obs = get_unified_observability()
        metrics_text = obs.export_prometheus_metrics()

        return metrics_text, 200, {"Content-Type": "text/plain; charset=utf-8"}

    except Exception as e:
        current_app.logger.error(f"Error exporting Prometheus metrics: {str(e)}")
        return "# Error exporting metrics", 500


# ======================================================================================
# ANOMALY DETECTION
# ======================================================================================
@api_bp.route("/observability/anomalies", methods=["GET"])
def detect_anomalies():
    """
    Detect anomalies using ML-based detection

    Returns:
    - Latency spikes (> 3x baseline)
    - Error rate spikes (> 2x baseline)
    - Traffic anomalies
    """
    try:
        obs = get_unified_observability()
        anomalies = obs.detect_anomalies()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"anomalies": anomalies, "count": len(anomalies)},
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to detect anomalies"}), 500


# ======================================================================================
# SERVICE DEPENDENCIES
# ======================================================================================
@api_bp.route("/observability/dependencies", methods=["GET"])
def get_service_dependencies():
    """
    Get service dependency graph

    Extracted from distributed traces
    Shows which services call which other services

    Returns:
    - Dependency map: service → [called services]
    - Visualization-ready format
    """
    try:
        obs = get_unified_observability()
        dependencies = obs.get_service_dependencies()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"dependencies": dependencies, "service_count": len(dependencies)},
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting service dependencies: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve service dependencies"}),
            500,
        )


# ======================================================================================
# STATISTICS & HEALTH
# ======================================================================================
@api_bp.route("/observability/statistics", methods=["GET"])
def get_observability_statistics():
    """
    Get overall observability system statistics

    Returns:
    - Traces: started, completed, active
    - Spans: created, active
    - Metrics: recorded, buffer sizes
    - Logs: recorded, buffer sizes
    - Anomalies: detected count
    """
    try:
        obs = get_unified_observability()
        stats = obs.get_statistics()

        return (
            jsonify(
                {"status": "success", "data": stats, "timestamp": datetime.now(UTC).isoformat()}
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve statistics"}), 500


@api_bp.route("/observability/health", methods=["GET"])
def observability_health_check():
    """
    Observability system health check

    Returns:
    - System status
    - Enabled features
    - Performance metrics
    """
    try:
        obs = get_unified_observability()
        stats = obs.get_statistics()

        health_data = {
            "status": "healthy",
            "features": {
                "distributed_tracing": "enabled",
                "metrics_collection": "enabled",
                "structured_logging": "enabled",
                "anomaly_detection": "enabled",
                "service_dependency_mapping": "enabled",
                "trace_correlation": "enabled",
                "w3c_trace_context": "enabled",
                "exemplars": "enabled",
            },
            "statistics": stats,
            "sla_targets": {
                "p99_latency_ms": obs.latency_p99_target,
                "error_rate_percent": obs.error_rate_target,
                "saturation_percent": obs.saturation_target,
            },
        }

        return (
            jsonify(
                {
                    "status": "success",
                    "data": health_data,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Observability health check failed: {str(e)}")
        return jsonify({"status": "error", "message": "Observability system unhealthy"}), 503


# ======================================================================================
# COMPLETE DASHBOARD DATA
# ======================================================================================
@api_bp.route("/observability/dashboard", methods=["GET"])
def get_dashboard_data():
    """
    Get complete dashboard data in ONE request

    This endpoint provides ALL data needed for a monitoring dashboard:
    - Golden Signals
    - Recent slow traces
    - Active anomalies
    - Service dependencies
    - System statistics

    Perfect for:
    - Grafana dashboards
    - Custom monitoring UIs
    - Real-time monitoring
    """
    try:
        time_window = request.args.get("time_window", 300, type=int)
        obs = get_unified_observability()

        # Get all data in parallel
        golden_signals = obs.get_golden_signals(time_window_seconds=time_window)
        slow_traces = obs.find_traces_by_criteria(min_duration_ms=100, limit=20)
        anomalies = obs.detect_anomalies()
        dependencies = obs.get_service_dependencies()
        statistics = obs.get_statistics()

        dashboard_data = {
            "golden_signals": golden_signals,
            "slow_traces": {"traces": slow_traces, "count": len(slow_traces)},
            "anomalies": {"alerts": anomalies, "count": len(anomalies)},
            "service_dependencies": dependencies,
            "statistics": statistics,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return jsonify({"status": "success", "data": dashboard_data}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve dashboard data"}), 500


# ======================================================================================
# INVESTIGATION WORKFLOW
# ======================================================================================
@api_bp.route("/observability/investigate", methods=["GET"])
def investigate_issue():
    """
    Multi-dimensional investigation workflow

    Query Parameters:
    - timestamp: ISO timestamp of the issue
    - metric_spike: Metric that spiked (latency, error_rate, traffic)

    This endpoint follows the investigation pattern from the requirements:
    1. Detect metric spike
    2. Find traces at that time
    3. Analyze slow/error traces
    4. Get correlated logs
    5. Identify root cause

    Returns complete investigation data!
    """
    try:
        timestamp_str = request.args.get("timestamp")
        metric_spike = request.args.get("metric_spike", "latency")

        if not timestamp_str:
            return jsonify({"status": "error", "message": "timestamp parameter required"}), 400

        obs = get_unified_observability()

        # Parse timestamp
        try:
            issue_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            issue_timestamp = issue_time.timestamp()
        except Exception:
            return jsonify({"status": "error", "message": "Invalid timestamp format"}), 400

        # Find traces around that time (±60 seconds)
        time_window_start = issue_timestamp - 60
        time_window_end = issue_timestamp + 60

        # Get recent traces
        all_traces = obs.find_traces_by_criteria(limit=1000)

        # Filter by time window
        relevant_traces = []
        for trace_summary in all_traces:
            try:
                trace_time = datetime.fromisoformat(
                    trace_summary["start_time"].replace("Z", "+00:00")
                )
                if time_window_start <= trace_time.timestamp() <= time_window_end:
                    relevant_traces.append(trace_summary)
            except Exception:
                continue

        # Sort by duration (slowest first)
        relevant_traces.sort(key=lambda t: t.get("duration_ms", 0), reverse=True)

        # Get top 5 slowest traces with full details
        investigation_traces = []
        for trace_summary in relevant_traces[:5]:
            trace_id = trace_summary["trace_id"]
            full_trace = obs.get_trace_with_correlation(trace_id)
            if full_trace:
                investigation_traces.append(full_trace)

        # Build investigation report
        investigation = {
            "issue_timestamp": timestamp_str,
            "metric_spike": metric_spike,
            "time_window": {"start": time_window_start, "end": time_window_end},
            "traces_found": len(relevant_traces),
            "top_slow_traces": investigation_traces,
            "analysis": {
                "avg_duration_ms": (
                    sum(t.get("duration_ms", 0) for t in relevant_traces) / len(relevant_traces)
                    if relevant_traces
                    else 0
                ),
                "error_count": sum(1 for t in relevant_traces if t.get("error_count", 0) > 0),
                "max_duration_ms": (
                    max(t.get("duration_ms", 0) for t in relevant_traces) if relevant_traces else 0
                ),
            },
            "recommendations": [
                f"Investigate bottleneck spans in trace {t['trace_id']}"
                for t in investigation_traces[:3]
            ],
        }

        return jsonify({"status": "success", "data": investigation}), 200

    except Exception as e:
        current_app.logger.error(f"Error during investigation: {str(e)}")
        return jsonify({"status": "error", "message": "Investigation failed"}), 500
