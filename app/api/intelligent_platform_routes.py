# app/api/intelligent_platform_routes.py
"""
INTELLIGENT SERVICE PLATFORM API ROUTES
Expose all intelligent platform services via REST API
"""

import uuid
from datetime import UTC, datetime

from flask import Blueprint, jsonify, request

from app.services.aiops_self_healing_service import (
    MetricType,
    TelemetryData,
    get_aiops_service,
)
from app.services.data_mesh_service import (
    DataContract,
    DataDomainType,
    SchemaCompatibility,
    get_data_mesh_service,
)
from app.services.edge_multicloud_service import (
    PlacementStrategy,
    get_edge_multicloud_service,
)
from app.services.gitops_policy_service import (
    GitOpsApp,
    get_gitops_service,
)
from app.services.sre_error_budget_service import (
    SLO,
    DeploymentStrategy,
    get_sre_service,
)
from app.services.workflow_orchestration_service import (
    WorkflowActivity,
    WorkflowDefinition,
    get_workflow_orchestration_service,
)

intelligent_platform_bp = Blueprint("intelligent_platform", __name__, url_prefix="/api/v1/platform")


# ======================================================================================
# DATA MESH ENDPOINTS
# ======================================================================================


@intelligent_platform_bp.route("/data-mesh/metrics", methods=["GET"])
def get_data_mesh_metrics():
    """Get Data Mesh metrics"""
    data_mesh = get_data_mesh_service()
    metrics = data_mesh.get_mesh_metrics()
    return jsonify({"ok": True, "data": metrics})


@intelligent_platform_bp.route("/data-mesh/contracts", methods=["POST"])
def create_data_contract():
    """Create data contract"""
    data = request.get_json()
    data_mesh = get_data_mesh_service()

    contract = DataContract(
        contract_id=data.get("contract_id", str(uuid.uuid4())),
        domain=DataDomainType(data["domain"]),
        name=data["name"],
        description=data["description"],
        schema_version=data["schema_version"],
        schema_definition=data["schema_definition"],
        compatibility_mode=SchemaCompatibility(data.get("compatibility_mode", "backward")),
        owners=data.get("owners", []),
        consumers=data.get("consumers", []),
        sla_guarantees=data.get("sla_guarantees", {}),
    )

    success = data_mesh.create_data_contract(contract)
    return jsonify({"ok": success, "data": {"contract_id": contract.contract_id}})


@intelligent_platform_bp.route("/data-mesh/quality/<product_id>", methods=["GET"])
def get_data_quality(product_id: str):
    """Get data quality summary"""
    data_mesh = get_data_mesh_service()
    summary = data_mesh.get_quality_summary(product_id)
    return jsonify({"ok": True, "data": summary})


# ======================================================================================
# AIOPS ENDPOINTS
# ======================================================================================


@intelligent_platform_bp.route("/aiops/metrics", methods=["GET"])
def get_aiops_metrics():
    """Get AIOps metrics"""
    aiops = get_aiops_service()
    metrics = aiops.get_aiops_metrics()
    return jsonify({"ok": True, "data": metrics})


@intelligent_platform_bp.route("/aiops/telemetry", methods=["POST"])
def collect_telemetry():
    """Collect telemetry data"""
    data = request.get_json()
    aiops = get_aiops_service()

    telemetry = TelemetryData(
        metric_id=str(uuid.uuid4()),
        service_name=data["service_name"],
        metric_type=MetricType(data["metric_type"]),
        value=data["value"],
        timestamp=datetime.now(UTC),
        labels=data.get("labels", {}),
        unit=data.get("unit", ""),
    )

    aiops.collect_telemetry(telemetry)
    return jsonify({"ok": True, "data": {"metric_id": telemetry.metric_id}})


@intelligent_platform_bp.route("/aiops/forecast/<service_name>", methods=["GET"])
def get_load_forecast(service_name: str):
    """Get load forecast"""
    metric_type = request.args.get("metric_type", "request_rate")
    hours_ahead = int(request.args.get("hours_ahead", 24))

    aiops = get_aiops_service()
    forecast = aiops.forecast_load(service_name, MetricType(metric_type), hours_ahead)

    if forecast:
        return jsonify(
            {
                "ok": True,
                "data": {
                    "forecast_id": forecast.forecast_id,
                    "predicted_load": forecast.predicted_load,
                    "confidence_interval": forecast.confidence_interval,
                    "model_accuracy": forecast.model_accuracy,
                },
            }
        )

    return jsonify({"ok": False, "error": "Insufficient data for forecast"})


@intelligent_platform_bp.route("/aiops/health/<service_name>", methods=["GET"])
def get_service_health(service_name: str):
    """Get service health status"""
    aiops = get_aiops_service()
    health = aiops.get_service_health(service_name)
    return jsonify({"ok": True, "data": health})


# ======================================================================================
# GITOPS ENDPOINTS
# ======================================================================================


@intelligent_platform_bp.route("/gitops/metrics", methods=["GET"])
def get_gitops_metrics():
    """Get GitOps metrics"""
    gitops = get_gitops_service()
    metrics = gitops.get_gitops_metrics()
    return jsonify({"ok": True, "data": metrics})


@intelligent_platform_bp.route("/gitops/apps", methods=["POST"])
def register_gitops_app():
    """Register GitOps application"""
    data = request.get_json()
    gitops = get_gitops_service()

    app = GitOpsApp(
        app_id=data.get("app_id", str(uuid.uuid4())),
        name=data["name"],
        namespace=data["namespace"],
        git_repo=data["git_repo"],
        git_path=data["git_path"],
        git_branch=data["git_branch"],
        sync_policy=data.get("sync_policy", {"auto_sync": False}),
        destination=data["destination"],
    )

    success = gitops.register_application(app)
    return jsonify({"ok": success, "data": {"app_id": app.app_id}})


@intelligent_platform_bp.route("/gitops/sync-status/<app_id>", methods=["GET"])
def get_app_sync_status(app_id: str):
    """Get application sync status"""
    gitops = get_gitops_service()
    status = gitops.get_sync_status(app_id)
    return jsonify({"ok": True, "data": status})


# ======================================================================================
# WORKFLOW ORCHESTRATION ENDPOINTS
# ======================================================================================


@intelligent_platform_bp.route("/workflows/metrics", methods=["GET"])
def get_workflow_metrics():
    """Get workflow metrics"""
    workflow_service = get_workflow_orchestration_service()
    metrics = workflow_service.get_metrics()
    return jsonify({"ok": True, "data": metrics})


@intelligent_platform_bp.route("/workflows", methods=["POST"])
def register_workflow():
    """Register workflow"""
    data = request.get_json()
    workflow_service = get_workflow_orchestration_service()

    activities = [
        WorkflowActivity(
            activity_id=act["activity_id"],
            name=act["name"],
            handler=act["handler"],
            input_data=act.get("input_data", {}),
            retry_policy=act.get("retry_policy", {"max_attempts": 3}),
            timeout_seconds=act.get("timeout_seconds", 300),
            compensation_handler=act.get("compensation_handler"),
        )
        for act in data.get("activities", [])
    ]

    workflow = WorkflowDefinition(
        workflow_id=data.get("workflow_id", str(uuid.uuid4())),
        name=data["name"],
        activities=activities,
        event_triggers=data.get("event_triggers", []),
        parallel_execution=data.get("parallel_execution", False),
    )

    success = workflow_service.register_workflow(workflow)
    return jsonify({"ok": success, "data": {"workflow_id": workflow.workflow_id}})


@intelligent_platform_bp.route("/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id: str):
    """Execute workflow"""
    workflow_service = get_workflow_orchestration_service()
    result = workflow_service.execute_workflow(workflow_id)

    if result:
        return jsonify(
            {
                "ok": True,
                "data": {
                    "workflow_id": result.workflow_id,
                    "status": result.status.value,
                    "started_at": result.started_at.isoformat() if result.started_at else None,
                    "completed_at": (
                        result.completed_at.isoformat() if result.completed_at else None
                    ),
                },
            }
        )

    return jsonify({"ok": False, "error": "Workflow not found"})


# ======================================================================================
# EDGE & MULTI-CLOUD ENDPOINTS
# ======================================================================================


@intelligent_platform_bp.route("/edge-multicloud/metrics", methods=["GET"])
def get_edge_multicloud_metrics():
    """Get edge & multi-cloud metrics"""
    edge_service = get_edge_multicloud_service()
    metrics = edge_service.get_metrics()
    return jsonify({"ok": True, "data": metrics})


@intelligent_platform_bp.route("/edge-multicloud/placement", methods=["POST"])
def place_workload():
    """Place workload across clouds and edge"""
    data = request.get_json()
    edge_service = get_edge_multicloud_service()

    placement = edge_service.place_workload(
        workload_name=data["workload_name"],
        requirements=data.get("requirements", {}),
        strategy=PlacementStrategy(data.get("strategy", "balanced")),
    )

    return jsonify(
        {
            "ok": True,
            "data": {
                "placement_id": placement.placement_id,
                "primary_region": placement.primary_region,
                "replica_regions": placement.replica_regions,
                "edge_locations": placement.edge_locations,
            },
        }
    )


# ======================================================================================
# SRE & ERROR BUDGET ENDPOINTS
# ======================================================================================


@intelligent_platform_bp.route("/sre/metrics", methods=["GET"])
def get_sre_metrics():
    """Get SRE metrics"""
    sre_service = get_sre_service()
    metrics = sre_service.get_sre_metrics()
    return jsonify({"ok": True, "data": metrics})


@intelligent_platform_bp.route("/sre/slo", methods=["POST"])
def create_slo():
    """Create SLO"""
    data = request.get_json()
    sre_service = get_sre_service()

    slo = SLO(
        slo_id=data.get("slo_id", str(uuid.uuid4())),
        service_name=data["service_name"],
        name=data["name"],
        description=data["description"],
        target_percentage=data["target_percentage"],
        measurement_window_days=data["measurement_window_days"],
        sli_type=data["sli_type"],
        threshold_value=data.get("threshold_value"),
    )

    success = sre_service.create_slo(slo)
    return jsonify({"ok": success, "data": {"slo_id": slo.slo_id}})


@intelligent_platform_bp.route("/sre/deployment-risk", methods=["POST"])
def assess_deployment_risk():
    """Assess deployment risk"""
    data = request.get_json()
    sre_service = get_sre_service()

    risk = sre_service.assess_deployment_risk(
        deployment_id=data.get("deployment_id", str(uuid.uuid4())),
        service_name=data["service_name"],
        strategy=DeploymentStrategy(data.get("strategy", "rolling")),
    )

    return jsonify(
        {
            "ok": True,
            "data": {
                "risk_id": risk.risk_id,
                "risk_score": risk.risk_score,
                "recommendation": risk.recommendation,
                "factors": risk.factors,
            },
        }
    )


@intelligent_platform_bp.route("/sre/canary", methods=["POST"])
def start_canary():
    """Start canary deployment"""
    data = request.get_json()
    sre_service = get_sre_service()

    canary = sre_service.start_canary_deployment(
        service_name=data["service_name"],
        canary_percentage=data["canary_percentage"],
        duration_minutes=data["duration_minutes"],
        success_criteria=data["success_criteria"],
    )

    return jsonify(
        {
            "ok": True,
            "data": {
                "deployment_id": canary.deployment_id,
                "service_name": canary.service_name,
                "canary_percentage": canary.canary_percentage,
            },
        }
    )


# ======================================================================================
# PLATFORM OVERVIEW
# ======================================================================================


@intelligent_platform_bp.route("/overview", methods=["GET"])
def get_platform_overview():
    """Get platform overview with all metrics"""
    data_mesh = get_data_mesh_service()
    aiops = get_aiops_service()
    gitops = get_gitops_service()
    workflow_service = get_workflow_orchestration_service()
    edge_service = get_edge_multicloud_service()
    sre_service = get_sre_service()

    overview = {
        "data_mesh": data_mesh.get_mesh_metrics(),
        "aiops": aiops.get_aiops_metrics(),
        "gitops": gitops.get_gitops_metrics(),
        "workflows": workflow_service.get_metrics(),
        "edge_multicloud": edge_service.get_metrics(),
        "sre": sre_service.get_sre_metrics(),
    }

    return jsonify({"ok": True, "data": overview})
