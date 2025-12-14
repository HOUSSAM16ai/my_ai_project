
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_data_mesh_refactor_verification():
    """
    Verifies that the Data Mesh endpoints have been successfully moved to their own router
    and that the legacy Intelligent Platform endpoints are updated/removed.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Verify New Data Mesh Contract Endpoint (POST /api/v1/data-mesh/contracts)
        # Note: The Blueprint maps it to /api/v1/data-mesh

        contract_payload = {
            "domain": "customer",
            "name": "Customer 360",
            "description": "Unified Customer View",
            "schema_version": "1.0",
            "schema_definition": {"type": "record", "fields": []}
        }

        # We need to mock the service dependency or expect a 500/401/422 if not mocked.
        # However, we are checking *reachability* primarily.
        # If the router is wired, we should get 422 (validation) or 500 (db) or 200.
        # We should definitely NOT get 404.

        response = await client.post("/api/v1/data-mesh/contracts", json=contract_payload)

        # We expect authentication failure or success or validation error, but NOT 404
        assert response.status_code != 404, "Data Mesh Contract endpoint not found at new location"

        # 2. Verify New Data Mesh Metrics Endpoint (GET /api/v1/data-mesh/metrics)
        response = await client.get("/api/v1/data-mesh/metrics")
        assert response.status_code != 404, "Data Mesh Metrics endpoint not found at new location"

        # 3. Verify Observability Metrics (GET /api/observability/metrics)
        response = await client.get("/api/observability/metrics")
        assert response.status_code != 404, "Observability Metrics endpoint not found"

        # 4. Verify AIOps Telemetry (POST /api/v1/platform/aiops/telemetry)
        # This one remained in platform router (intelligent_platform.py) but we updated the code
        telemetry_payload = {
            "service_name": "test-service",
            "metric_type": "gauge",
            "value": 42.0
        }
        response = await client.post("/api/v1/platform/aiops/telemetry", json=telemetry_payload)
        assert response.status_code != 404, "Telemetry endpoint lost"

        # 5. Verify Dummy Endpoints are GONE
        # The intelligent_platform_blueprint.py used to have /api/v1/platform/data-mesh/contracts
        # Wait, the Blueprint name is "api/v1/platform".
        # The old route was @router.post("/data-mesh/contracts") inside that blueprint.
        # So path was /api/v1/platform/data-mesh/contracts.
        # I REMOVED that route from the blueprint and the router.
        # So it SHOULD return 404 now.

        response = await client.post("/api/v1/platform/data-mesh/contracts", json=contract_payload)
        assert response.status_code == 404, "Legacy Data Mesh endpoint should be removed from Platform router"

