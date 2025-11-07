# app/api/comprehensive_metrics_routes.py
# ======================================================================================
# ==  COMPREHENSIVE METRICS ROUTES - MEASURE EVERYTHING (v1.0 SUPERHUMAN)         ==
# ======================================================================================
"""
مسارات القياس الشامل - Comprehensive Metrics Routes

نظام مسارات API الخارق للقياس الشامل يتفوق على جميع الشركات العملاقة

Exposes all metrics through REST APIs:
✅ Infrastructure Metrics (CPU, Memory, Disk, Network)
✅ AI Model Performance Metrics (Accuracy, Latency, Cost, Drift)
✅ User Analytics & Business Metrics (Engagement, Conversion, Retention, NPS)
✅ Security Metrics (already exists in security_metrics_engine.py)
✅ SLO/SLI Tracking (already exists in api_slo_sli_service.py)
"""

from datetime import UTC, datetime

from flask import current_app, jsonify, request

from app.api import api_bp
from app.services.ai_model_metrics_service import ModelType, get_ai_model_service
from app.services.api_observability_service import monitor_performance
from app.services.api_security_service import rate_limit
from app.services.infrastructure_metrics_service import get_infrastructure_service
from app.services.user_analytics_metrics_service import (
    EventType,
    get_user_analytics_service,
)


# ======================================================================================
# INFRASTRUCTURE METRICS ENDPOINTS
# ======================================================================================


@api_bp.route("/metrics/infrastructure/summary", methods=["GET"])
@rate_limit
@monitor_performance
def get_infrastructure_summary():
    """
    Get comprehensive infrastructure metrics summary

    Returns:
        - CPU usage and load averages
        - Memory utilization
        - Disk usage and I/O
        - Network traffic and connections
        - System uptime and health status
    """
    try:
        infra_service = get_infrastructure_service()
        summary = infra_service.get_metrics_summary()

        return jsonify({"status": "success", "data": summary}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting infrastructure summary: {str(e)}")
        return (
            jsonify(
                {"status": "error", "message": "Failed to retrieve infrastructure metrics"}
            ),
            500,
        )


@api_bp.route("/metrics/infrastructure/cpu", methods=["GET"])
@rate_limit
@monitor_performance
def get_cpu_metrics():
    """Get detailed CPU metrics"""
    try:
        infra_service = get_infrastructure_service()
        cpu = infra_service.collect_cpu_metrics()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "usage_percent": cpu.usage_percent,
                        "user_percent": cpu.user_percent,
                        "system_percent": cpu.system_percent,
                        "idle_percent": cpu.idle_percent,
                        "load_average": {
                            "1m": cpu.load_average_1m,
                            "5m": cpu.load_average_5m,
                            "15m": cpu.load_average_15m,
                        },
                        "cores": cpu.core_count,
                        "timestamp": cpu.timestamp.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting CPU metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve CPU metrics"}),
            500,
        )


@api_bp.route("/metrics/infrastructure/memory", methods=["GET"])
@rate_limit
@monitor_performance
def get_memory_metrics():
    """Get detailed memory metrics"""
    try:
        infra_service = get_infrastructure_service()
        memory = infra_service.collect_memory_metrics()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "total_gb": memory.total_bytes / (1024**3),
                        "used_gb": memory.used_bytes / (1024**3),
                        "available_gb": memory.available_bytes / (1024**3),
                        "used_percent": memory.used_percent,
                        "swap": {
                            "total_gb": memory.swap_total_bytes / (1024**3),
                            "used_gb": memory.swap_used_bytes / (1024**3),
                            "percent": memory.swap_percent,
                        },
                        "timestamp": memory.timestamp.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting memory metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve memory metrics"}),
            500,
        )


@api_bp.route("/metrics/infrastructure/disk", methods=["GET"])
@rate_limit
@monitor_performance
def get_disk_metrics():
    """Get detailed disk metrics"""
    try:
        mount_point = request.args.get("mount_point", "/")
        infra_service = get_infrastructure_service()
        disk = infra_service.collect_disk_metrics(mount_point)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "total_gb": disk.total_bytes / (1024**3),
                        "used_gb": disk.used_bytes / (1024**3),
                        "free_gb": disk.free_bytes / (1024**3),
                        "used_percent": disk.used_percent,
                        "io": {
                            "read_mbps": disk.read_bytes_per_sec / (1024**2),
                            "write_mbps": disk.write_bytes_per_sec / (1024**2),
                            "read_iops": disk.read_iops,
                            "write_iops": disk.write_iops,
                        },
                        "mount_point": disk.mount_point,
                        "timestamp": disk.timestamp.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting disk metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve disk metrics"}),
            500,
        )


@api_bp.route("/metrics/infrastructure/network", methods=["GET"])
@rate_limit
@monitor_performance
def get_network_metrics():
    """Get detailed network metrics"""
    try:
        infra_service = get_infrastructure_service()
        network = infra_service.collect_network_metrics()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "throughput": {
                            "sent_mbps": network.bytes_sent_per_sec / (1024**2),
                            "recv_mbps": network.bytes_recv_per_sec / (1024**2),
                        },
                        "packets": {
                            "sent_per_sec": network.packets_sent_per_sec,
                            "recv_per_sec": network.packets_recv_per_sec,
                        },
                        "errors": {
                            "in": network.errors_in,
                            "out": network.errors_out,
                        },
                        "drops": {
                            "in": network.drops_in,
                            "out": network.drops_out,
                        },
                        "connections": network.connections_active,
                        "timestamp": network.timestamp.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting network metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve network metrics"}),
            500,
        )


@api_bp.route("/metrics/infrastructure/availability/<service_name>", methods=["GET"])
@rate_limit
@monitor_performance
def get_service_availability(service_name):
    """Get availability metrics for a service"""
    try:
        infra_service = get_infrastructure_service()
        availability = infra_service.get_availability_metrics(service_name)

        if not availability:
            return (
                jsonify({"status": "error", "message": f"Service {service_name} not found"}),
                404,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "service_name": availability.service_name,
                        "availability_percent": availability.availability_percent,
                        "uptime_hours": availability.uptime_seconds / 3600,
                        "downtime_hours": availability.downtime_seconds / 3600,
                        "incidents": availability.incidents_count,
                        "mtbf_hours": availability.mtbf_seconds / 3600,
                        "mttr_minutes": availability.mttr_seconds / 60,
                        "sla_target": availability.sla_target,
                        "sla_compliance": availability.sla_compliance,
                        "last_incident": (
                            availability.last_incident.isoformat()
                            if availability.last_incident
                            else None
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting availability metrics: {str(e)}")
        return (
            jsonify(
                {"status": "error", "message": "Failed to retrieve availability metrics"}
            ),
            500,
        )


@api_bp.route("/metrics/infrastructure/prometheus", methods=["GET"])
@rate_limit
def export_prometheus_metrics():
    """Export infrastructure metrics in Prometheus format"""
    try:
        infra_service = get_infrastructure_service()
        metrics = infra_service.export_prometheus_metrics()

        return metrics, 200, {"Content-Type": "text/plain; charset=utf-8"}

    except Exception as e:
        current_app.logger.error(f"Error exporting Prometheus metrics: {str(e)}")
        return "# Error exporting metrics\n", 500


# ======================================================================================
# AI MODEL METRICS ENDPOINTS
# ======================================================================================


@api_bp.route("/metrics/ai/models", methods=["GET"])
@rate_limit
@monitor_performance
def get_ai_models_summary():
    """Get summary of all AI models being tracked"""
    try:
        ai_service = get_ai_model_service()
        summary = ai_service.export_metrics_summary()

        return jsonify({"status": "success", "data": summary}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting AI models summary: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve AI models metrics"}),
            500,
        )


@api_bp.route("/metrics/ai/models/<model_name>/<model_version>", methods=["GET"])
@rate_limit
@monitor_performance
def get_model_metrics(model_name, model_version):
    """Get detailed metrics for a specific model"""
    try:
        ai_service = get_ai_model_service()
        snapshot = ai_service.get_model_performance_snapshot(model_name, model_version)

        if not snapshot:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Model {model_name}:{model_version} not found",
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "model_name": snapshot.model_name,
                        "model_version": snapshot.model_version,
                        "health_score": snapshot.health_score,
                        "latency": {
                            "p50_ms": snapshot.latency_metrics.p50_ms,
                            "p95_ms": snapshot.latency_metrics.p95_ms,
                            "p99_ms": snapshot.latency_metrics.p99_ms,
                            "mean_ms": snapshot.latency_metrics.mean_ms,
                        },
                        "cost": {
                            "total_usd": snapshot.cost_metrics.total_cost_usd,
                            "per_request": snapshot.cost_metrics.cost_per_request,
                            "per_1k_tokens": snapshot.cost_metrics.cost_per_1k_tokens,
                        },
                        "drift": (
                            {
                                "status": snapshot.drift_metrics.drift_status.value,
                                "score": snapshot.drift_metrics.drift_score,
                                "data_quality": snapshot.drift_metrics.data_quality_score,
                            }
                            if snapshot.drift_metrics
                            else None
                        ),
                        "recommendations": snapshot.recommendations,
                        "timestamp": snapshot.timestamp.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting model metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve model metrics"}),
            500,
        )


@api_bp.route("/metrics/ai/models/register", methods=["POST"])
@rate_limit
@monitor_performance
def register_ai_model():
    """
    Register a new AI model for tracking

    Request body:
    {
        "model_name": "gpt-4",
        "model_version": "1.0",
        "model_type": "nlp_generation",
        "metadata": {}
    }
    """
    try:
        data = request.get_json()
        model_name = data.get("model_name")
        model_version = data.get("model_version")
        model_type_str = data.get("model_type")
        metadata = data.get("metadata", {})

        if not all([model_name, model_version, model_type_str]):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing required fields: model_name, model_version, model_type",
                    }
                ),
                400,
            )

        try:
            model_type = ModelType[model_type_str.upper()]
        except KeyError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Invalid model_type. Valid options: {[t.name for t in ModelType]}",
                    }
                ),
                400,
            )

        ai_service = get_ai_model_service()
        ai_service.register_model(model_name, model_version, model_type, metadata)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Model {model_name}:{model_version} registered successfully",
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error registering model: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to register model"}),
            500,
        )


@api_bp.route("/metrics/ai/inferences/record", methods=["POST"])
@rate_limit
@monitor_performance
def record_inference():
    """
    Record an AI model inference

    Request body:
    {
        "model_name": "gpt-4",
        "model_version": "1.0",
        "latency_ms": 150.5,
        "input_tokens": 100,
        "output_tokens": 200,
        "cost_usd": 0.005,
        "prediction": "...",
        "ground_truth": "...",
        "metadata": {}
    }
    """
    try:
        data = request.get_json()
        model_name = data.get("model_name")
        model_version = data.get("model_version")
        latency_ms = data.get("latency_ms")

        if not all([model_name, model_version, latency_ms is not None]):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing required fields: model_name, model_version, latency_ms",
                    }
                ),
                400,
            )

        ai_service = get_ai_model_service()
        inference_id = ai_service.record_inference(
            model_name=model_name,
            model_version=model_version,
            latency_ms=latency_ms,
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            cost_usd=data.get("cost_usd", 0.0),
            prediction=data.get("prediction"),
            ground_truth=data.get("ground_truth"),
            metadata=data.get("metadata"),
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "inference_id": inference_id,
                    "message": "Inference recorded successfully",
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error recording inference: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to record inference"}),
            500,
        )


# ======================================================================================
# USER ANALYTICS METRICS ENDPOINTS
# ======================================================================================


@api_bp.route("/metrics/users/summary", methods=["GET"])
@rate_limit
@monitor_performance
def get_user_analytics_summary():
    """Get comprehensive user analytics summary"""
    try:
        analytics_service = get_user_analytics_service()
        summary = analytics_service.export_metrics_summary()

        return jsonify({"status": "success", "data": summary}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting user analytics summary: {str(e)}")
        return (
            jsonify(
                {"status": "error", "message": "Failed to retrieve user analytics metrics"}
            ),
            500,
        )


@api_bp.route("/metrics/users/engagement", methods=["GET"])
@rate_limit
@monitor_performance
def get_engagement_metrics():
    """Get user engagement metrics (DAU, WAU, MAU, etc.)"""
    try:
        time_window = request.args.get("time_window", "30d")
        analytics_service = get_user_analytics_service()
        engagement = analytics_service.get_engagement_metrics(time_window)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "dau": engagement.dau,
                        "wau": engagement.wau,
                        "mau": engagement.mau,
                        "avg_session_duration": engagement.avg_session_duration,
                        "avg_sessions_per_user": engagement.avg_sessions_per_user,
                        "avg_events_per_session": engagement.avg_events_per_session,
                        "bounce_rate": engagement.bounce_rate,
                        "return_rate": engagement.return_rate,
                        "time_window": engagement.time_window,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting engagement metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve engagement metrics"}),
            500,
        )


@api_bp.route("/metrics/users/conversion", methods=["GET"])
@rate_limit
@monitor_performance
def get_conversion_metrics():
    """Get conversion metrics"""
    try:
        conversion_event = request.args.get("conversion_event", "conversion")
        analytics_service = get_user_analytics_service()
        conversion = analytics_service.get_conversion_metrics(conversion_event)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "conversion_rate": conversion.conversion_rate,
                        "total_conversions": conversion.total_conversions,
                        "total_visitors": conversion.total_visitors,
                        "avg_time_to_convert": conversion.avg_time_to_convert,
                        "conversion_value": conversion.conversion_value,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting conversion metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve conversion metrics"}),
            500,
        )


@api_bp.route("/metrics/users/retention", methods=["GET"])
@rate_limit
@monitor_performance
def get_retention_metrics():
    """Get user retention metrics"""
    try:
        analytics_service = get_user_analytics_service()
        retention = analytics_service.get_retention_metrics()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "day_1_retention": retention.day_1_retention,
                        "day_7_retention": retention.day_7_retention,
                        "day_30_retention": retention.day_30_retention,
                        "cohort_size": retention.cohort_size,
                        "churn_rate": retention.churn_rate,
                        "avg_lifetime_days": retention.avg_lifetime_days,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting retention metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve retention metrics"}),
            500,
        )


@api_bp.route("/metrics/users/nps", methods=["GET"])
@rate_limit
@monitor_performance
def get_nps_metrics():
    """Get Net Promoter Score (NPS) metrics"""
    try:
        analytics_service = get_user_analytics_service()
        nps = analytics_service.get_nps_metrics()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "nps_score": nps.nps_score,
                        "promoters_percent": nps.promoters_percent,
                        "passives_percent": nps.passives_percent,
                        "detractors_percent": nps.detractors_percent,
                        "total_responses": nps.total_responses,
                        "avg_score": nps.avg_score,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting NPS metrics: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve NPS metrics"}),
            500,
        )


@api_bp.route("/metrics/users/events/track", methods=["POST"])
@rate_limit
@monitor_performance
def track_user_event():
    """
    Track a user event

    Request body:
    {
        "user_id": 123,
        "event_type": "page_view",
        "event_name": "home_page_view",
        "session_id": "abc123",
        "properties": {},
        "page_url": "/home"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        event_type_str = data.get("event_type")
        event_name = data.get("event_name")

        if not all([user_id, event_type_str, event_name]):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing required fields: user_id, event_type, event_name",
                    }
                ),
                400,
            )

        try:
            event_type = EventType[event_type_str.upper()]
        except KeyError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Invalid event_type. Valid options: {[t.name for t in EventType]}",
                    }
                ),
                400,
            )

        analytics_service = get_user_analytics_service()
        event_id = analytics_service.track_event(
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            session_id=data.get("session_id"),
            properties=data.get("properties"),
            page_url=data.get("page_url"),
            device_type=data.get("device_type"),
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "event_id": event_id,
                    "message": "Event tracked successfully",
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error tracking event: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to track event"}),
            500,
        )


@api_bp.route("/metrics/users/nps/record", methods=["POST"])
@rate_limit
@monitor_performance
def record_nps_response():
    """
    Record an NPS response

    Request body:
    {
        "user_id": 123,
        "score": 9,
        "comment": "Great product!"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        score = data.get("score")

        if user_id is None or score is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing required fields: user_id, score",
                    }
                ),
                400,
            )

        if not 0 <= score <= 10:
            return (
                jsonify(
                    {"status": "error", "message": "Score must be between 0 and 10"}
                ),
                400,
            )

        analytics_service = get_user_analytics_service()
        analytics_service.record_nps_response(
            user_id=user_id, score=score, comment=data.get("comment", "")
        )

        return (
            jsonify(
                {"status": "success", "message": "NPS response recorded successfully"}
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error recording NPS response: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to record NPS response"}),
            500,
        )


# ======================================================================================
# UNIFIED METRICS DASHBOARD ENDPOINT
# ======================================================================================


@api_bp.route("/metrics/dashboard", methods=["GET"])
@rate_limit
@monitor_performance
def get_unified_metrics_dashboard():
    """
    Get unified metrics dashboard with all key metrics

    Returns comprehensive dashboard with:
    - Infrastructure health
    - AI model performance
    - User engagement
    - Business metrics
    """
    try:
        infra_service = get_infrastructure_service()
        ai_service = get_ai_model_service()
        analytics_service = get_user_analytics_service()

        # Collect all metrics
        infra_summary = infra_service.get_metrics_summary()
        ai_summary = ai_service.export_metrics_summary()
        user_summary = analytics_service.export_metrics_summary()

        dashboard = {
            "timestamp": datetime.now(UTC).isoformat(),
            "infrastructure": {
                "status": infra_summary["status"],
                "cpu_percent": infra_summary["cpu"]["current_percent"],
                "memory_percent": infra_summary["memory"]["used_percent"],
                "disk_percent": infra_summary["disk"]["used_percent"],
                "uptime_hours": infra_summary["uptime_seconds"] / 3600,
            },
            "ai_models": {
                "total_models": ai_summary["total_models"],
                "total_inferences": ai_summary["total_inferences"],
                "models": ai_summary.get("models", {}),
            },
            "users": {
                "dau": user_summary["engagement"]["dau"],
                "mau": user_summary["engagement"]["mau"],
                "conversion_rate": user_summary["conversion"]["conversion_rate"],
                "nps_score": user_summary["nps"]["score"],
                "total_users": user_summary["total_users"],
            },
            "health_summary": {
                "infrastructure": infra_summary["status"],
                "overall_health": (
                    "healthy"
                    if infra_summary["status"] == "healthy"
                    and user_summary["engagement"]["dau"] > 0
                    else "degraded"
                ),
            },
        }

        return jsonify({"status": "success", "data": dashboard}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting unified dashboard: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve dashboard metrics"}),
            500,
        )
