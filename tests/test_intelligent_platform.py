# tests/test_intelligent_platform.py
"""
Tests for Intelligent Service Platform
"""

from datetime import UTC, datetime

from app.services.aiops_self_healing_service import MetricType, TelemetryData, get_aiops_service
from app.services.data_mesh_service import (BoundedContext, DataContract, DataDomainType,
                                            DataProduct, DataQualityMetrics, SchemaCompatibility,
                                            get_data_mesh_service)
from app.services.edge_multicloud_service import PlacementStrategy, get_edge_multicloud_service
from app.services.gitops_policy_service import GitOpsApp, get_gitops_service
from app.services.sre_error_budget_service import SLO, DeploymentStrategy, get_sre_service
from app.services.workflow_orchestration_service import (WorkflowActivity, WorkflowDefinition,
                                                         get_workflow_orchestration_service)
from tests._helpers import parse_response_json


class TestDataMeshService:
    """Test Data Mesh service"""

    def test_register_bounded_context(self):
        """Test registering bounded context"""
        data_mesh = get_data_mesh_service()

        context = BoundedContext(
            context_id="test-ctx-1",
            domain=DataDomainType.USER_MANAGEMENT,
            name="Test Context",
            description="Test bounded context",
            data_products=[],
            upstream_contexts=[],
            downstream_contexts=[],
            governance_policies={},
        )

        success = data_mesh.register_bounded_context(context)
        assert success

        retrieved = data_mesh.get_bounded_context("test-ctx-1")
        assert retrieved is not None
        assert retrieved.name == "Test Context"

    def test_create_data_contract(self):
        """Test creating data contract"""
        data_mesh = get_data_mesh_service()

        contract = DataContract(
            contract_id="test-contract-1",
            domain=DataDomainType.USER_MANAGEMENT,
            name="Test Contract",
            description="Test data contract",
            schema_version="1.0.0",
            schema_definition={
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            compatibility_mode=SchemaCompatibility.BACKWARD,
            owners=["test-team"],
            consumers=[],
            sla_guarantees={},
        )

        success = data_mesh.create_data_contract(contract)
        assert success

    def test_record_quality_metrics(self):
        """Test recording quality metrics"""
        data_mesh = get_data_mesh_service()

        # First create a product
        product = DataProduct(
            product_id="test-product-1",
            name="Test Product",
            domain=DataDomainType.USER_MANAGEMENT,
            description="Test product",
            owner_team="test-team",
            contracts=[],
            quality_metrics={},
            access_patterns=[],
            lineage={},
        )
        data_mesh.register_data_product(product)

        metrics = DataQualityMetrics(
            product_id="test-product-1",
            timestamp=datetime.now(UTC),
            completeness=0.98,
            accuracy=0.99,
            consistency=0.97,
            timeliness=0.95,
            freshness_seconds=45,
            volume=1000,
            error_rate=0.01,
        )

        data_mesh.record_quality_metrics(metrics)

        summary = data_mesh.get_quality_summary("test-product-1")
        assert summary is not None
        assert summary["avg_completeness"] >= 0.9


class TestAIOpsService:
    """Test AIOps service"""

    def test_collect_telemetry(self):
        """Test collecting telemetry"""
        aiops = get_aiops_service()

        telemetry = TelemetryData(
            metric_id="test-metric-1",
            service_name="test-service",
            metric_type=MetricType.LATENCY,
            value=100.0,
            timestamp=datetime.now(UTC),
            labels={},
            unit="ms",
        )

        aiops.collect_telemetry(telemetry)

        # Collect more to build baseline
        for i in range(20):
            t = TelemetryData(
                metric_id=f"test-metric-{i}",
                service_name="test-service",
                metric_type=MetricType.LATENCY,
                value=95.0 + i,
                timestamp=datetime.now(UTC),
            )
            aiops.collect_telemetry(t)

    def test_get_service_health(self):
        """Test getting service health"""
        aiops = get_aiops_service()

        health = aiops.get_service_health("test-service")
        assert health is not None
        assert "service_name" in health
        assert health["service_name"] == "test-service"


class TestGitOpsService:
    """Test GitOps service"""

    def test_register_application(self):
        """Test registering GitOps application"""
        gitops = get_gitops_service()

        app = GitOpsApp(
            app_id="test-app-1",
            name="Test App",
            namespace="default",
            git_repo="https://github.com/test/repo",
            git_path="manifests/",
            git_branch="main",
            sync_policy={"auto_sync": False},
            destination={"server": "localhost", "namespace": "default"},
        )

        success = gitops.register_application(app)
        assert success

    def test_policy_evaluation(self):
        """Test policy evaluation"""
        gitops = get_gitops_service()

        resource = {
            "kind": "Deployment",
            "metadata": {"name": "test-deployment"},
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{"name": "test", "securityContext": {"privileged": True}}]
                    }
                }
            },
        }

        # Should violate the no-privileged-containers policy
        decision = gitops.admit_resource(resource)
        assert not decision.allowed


class TestWorkflowOrchestration:
    """Test Workflow Orchestration service"""

    def test_register_workflow(self):
        """Test registering workflow"""
        workflow_service = get_workflow_orchestration_service()

        workflow = WorkflowDefinition(
            workflow_id="test-workflow-1",
            name="Test Workflow",
            activities=[
                WorkflowActivity(
                    activity_id="activity-1",
                    name="Test Activity",
                    handler="test_handler",
                    input_data={},
                    retry_policy={"max_attempts": 3},
                )
            ],
            event_triggers=[],
            parallel_execution=False,
        )

        success = workflow_service.register_workflow(workflow)
        assert success

    def test_get_metrics(self):
        """Test getting workflow metrics"""
        workflow_service = get_workflow_orchestration_service()

        metrics = workflow_service.get_metrics()
        assert "total_workflows" in metrics


class TestEdgeMultiCloud:
    """Test Edge & Multi-Cloud service"""

    def test_place_workload(self):
        """Test workload placement"""
        edge_service = get_edge_multicloud_service()

        placement = edge_service.place_workload(
            workload_name="test-workload",
            requirements={"capabilities": ["compute"], "target_latency_ms": 100},
            strategy=PlacementStrategy.BALANCED,
        )

        assert placement is not None
        assert placement.primary_region is not None

    def test_get_metrics(self):
        """Test getting metrics"""
        edge_service = get_edge_multicloud_service()

        metrics = edge_service.get_metrics()
        assert "total_regions" in metrics
        assert metrics["total_regions"] > 0


class TestSREService:
    """Test SRE & Error Budget service"""

    def test_create_slo(self):
        """Test creating SLO"""
        sre_service = get_sre_service()

        slo = SLO(
            slo_id="test-slo-1",
            service_name="test-service",
            name="Test SLO",
            description="Test SLO",
            target_percentage=99.9,
            measurement_window_days=30,
            sli_type="availability",
        )

        success = sre_service.create_slo(slo)
        assert success

    def test_deployment_risk_assessment(self):
        """Test deployment risk assessment"""
        sre_service = get_sre_service()

        # Create SLO first
        slo = SLO(
            slo_id="test-slo-2",
            service_name="test-service-2",
            name="Test SLO 2",
            description="Test SLO 2",
            target_percentage=99.9,
            measurement_window_days=30,
            sli_type="availability",
        )
        sre_service.create_slo(slo)

        risk = sre_service.assess_deployment_risk(
            deployment_id="test-deploy-1",
            service_name="test-service-2",
            strategy=DeploymentStrategy.CANARY,
        )

        assert risk is not None
        assert 0 <= risk.risk_score <= 1
        assert risk.recommendation is not None


class TestIntelligentPlatformAPI:
    """Test Intelligent Platform API endpoints"""

    def test_data_mesh_metrics_endpoint(self, client):
        """Test Data Mesh metrics endpoint"""
        response = client.get("/api/v1/platform/data-mesh/metrics")
        assert response.status_code == 200
        data = parse_response_json(response)
        assert data["ok"] is True
        assert "data" in data

    def test_aiops_metrics_endpoint(self, client):
        """Test AIOps metrics endpoint"""
        response = client.get("/api/v1/platform/aiops/metrics")
        assert response.status_code == 200
        data = parse_response_json(response)
        assert data["ok"] is True

    def test_gitops_metrics_endpoint(self, client):
        """Test GitOps metrics endpoint"""
        response = client.get("/api/v1/platform/gitops/metrics")
        assert response.status_code == 200
        data = parse_response_json(response)
        assert data["ok"] is True

    def test_platform_overview_endpoint(self, client):
        """Test platform overview endpoint"""
        response = client.get("/api/v1/platform/overview")
        assert response.status_code == 200
        data = parse_response_json(response)
        assert data["ok"] is True
        assert "data_mesh" in data["data"]
        assert "aiops" in data["data"]
        assert "gitops" in data["data"]
        assert "workflows" in data["data"]
        assert "edge_multicloud" in data["data"]
        assert "sre" in data["data"]

    def test_create_data_contract_endpoint(self, client):
        """Test creating data contract via API"""
        response = client.post(
            "/api/v1/platform/data-mesh/contracts",
            json={
                "domain": "user_management",
                "name": "API Test Contract",
                "description": "Test",
                "schema_version": "1.0.0",
                "schema_definition": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                },
            },
        )
        assert response.status_code == 200
        data = parse_response_json(response)
        assert data["ok"] is True

    def test_collect_telemetry_endpoint(self, client):
        """Test collecting telemetry via API"""
        response = client.post(
            "/api/v1/platform/aiops/telemetry",
            json={
                "service_name": "api-test-service",
                "metric_type": "latency",
                "value": 125.5,
            },
        )
        assert response.status_code == 200
        data = parse_response_json(response)
        assert data["ok"] is True
