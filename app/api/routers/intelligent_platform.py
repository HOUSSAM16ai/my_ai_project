import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.aiops_self_healing_service import (
    AIOpsService,
    MetricType,
    TelemetryData,
    get_aiops_service,
)
from app.services.data_mesh_service import (
    DataContract,
    DataDomainType,
    DataMeshService,
    DataProductStatus,
    SchemaCompatibility,
    get_data_mesh_service,
)
from app.services.edge_multicloud_service import (
    EdgeMultiCloudService,
    get_edge_multicloud_service,
)
from app.services.gitops_policy_service import (
    GitOpsService,
    get_gitops_service,
)
from app.services.sre_error_budget_service import (
    SREErrorBudgetService,
    get_sre_service,
)
from app.services.workflow_orchestration_service import (
    WorkflowOrchestrationService,
    get_workflow_orchestration_service,
)

router = APIRouter(
    prefix="/api/v1/platform",
    tags=["Intelligent Platform"],
)


# --- Pydantic Models for Request Bodies ---


class CreateDataContractRequest(BaseModel):
    domain: DataDomainType
    name: str
    description: str
    schema_version: str
    schema_definition: dict[str, Any]
    compatibility_mode: SchemaCompatibility = SchemaCompatibility.BACKWARD
    owners: list[str] = Field(default_factory=list)
    consumers: list[str] = Field(default_factory=list)
    sla_guarantees: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectTelemetryRequest(BaseModel):
    service_name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    unit: str = ""
    timestamp: datetime | None = None


# --- Endpoints ---


@router.get("/data-mesh/metrics")
async def get_data_mesh_metrics(
    service: DataMeshService = Depends(get_data_mesh_service),
):
    """Get Data Mesh metrics"""
    # The test expects {"ok": True, "data": ...}
    # We can fetch real metrics from the service
    metrics = service.get_mesh_metrics()
    return {"ok": True, "data": metrics}


@router.get("/aiops/metrics")
async def get_aiops_metrics(
    service: AIOpsService = Depends(get_aiops_service),
):
    """Get AIOps metrics"""
    metrics = service.get_aiops_metrics()
    return {"ok": True, "data": metrics}


@router.get("/gitops/metrics")
async def get_gitops_metrics(
    service: GitOpsService = Depends(get_gitops_service),
):
    """Get GitOps metrics"""
    metrics = service.get_gitops_metrics()
    return {"ok": True, "data": metrics}


@router.get("/overview")
async def get_platform_overview(
    data_mesh: DataMeshService = Depends(get_data_mesh_service),
    aiops: AIOpsService = Depends(get_aiops_service),
    gitops: GitOpsService = Depends(get_gitops_service),
    workflows: WorkflowOrchestrationService = Depends(get_workflow_orchestration_service),
    edge: EdgeMultiCloudService = Depends(get_edge_multicloud_service),
    sre: SREErrorBudgetService = Depends(get_sre_service),
):
    """Get platform overview"""
    return {
        "ok": True,
        "data": {
            "data_mesh": data_mesh.get_mesh_metrics(),
            "aiops": aiops.get_aiops_metrics(),
            "gitops": gitops.get_gitops_metrics(),
            "workflows": workflows.get_metrics(),
            "edge_multicloud": edge.get_metrics(),
            "sre": sre.get_sre_metrics(),
        },
    }


@router.post("/data-mesh/contracts")
async def create_data_contract(
    request: CreateDataContractRequest,
    service: DataMeshService = Depends(get_data_mesh_service),
):
    """Create data contract"""

    # Map Pydantic model to Dataclass
    contract = DataContract(
        contract_id=str(uuid.uuid4()),
        domain=request.domain,
        name=request.name,
        description=request.description,
        schema_version=request.schema_version,
        schema_definition=request.schema_definition,
        compatibility_mode=request.compatibility_mode,
        owners=request.owners,
        consumers=request.consumers,
        sla_guarantees=request.sla_guarantees,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        status=DataProductStatus.ACTIVE,
        metadata=request.metadata,
    )

    result = service.create_data_contract(contract)
    return {"ok": result}


@router.post("/aiops/telemetry")
async def collect_telemetry(
    request: CollectTelemetryRequest,
    service: AIOpsService = Depends(get_aiops_service),
):
    """Collect telemetry"""

    # Map Pydantic model to Dataclass
    telemetry = TelemetryData(
        metric_id=str(uuid.uuid4()),
        service_name=request.service_name,
        metric_type=request.metric_type,
        value=request.value,
        timestamp=request.timestamp or datetime.now(UTC),
        labels=request.labels,
        unit=request.unit,
    )

    service.collect_telemetry(telemetry)
    return {"ok": True}
