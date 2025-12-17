from __future__ import annotations

import logging
from typing import Any

import pytest
from httpx import AsyncClient

# Remove the explicit dependency injection of the service in the test signature
# because we only need the API client to test the contract.
# If we need internal state, we can import the singleton or use `get_platform_boundary_service`.

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_observability_schema_contract_metrics(
    async_client: AsyncClient,
):
    """
    Refactoring Safety Check:
    Ensures that the /metrics endpoint returns the strict schema.
    """
    # 1. Call the endpoint
    response = await async_client.get("/api/observability/metrics")

    # 2. Assert status code
    assert response.status_code == 200

    # 3. Assert Response Structure (The "Safe" Refactor Check)
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "metrics" in data

    metrics = data["metrics"]
    assert "api_performance" in metrics
    assert "aiops_health" in metrics


@pytest.mark.asyncio
async def test_observability_schema_contract_aiops(
    async_client: AsyncClient,
):
    """
    Refactoring Safety Check:
    Ensures that /metrics/aiops returns the legacy {"ok": True, "data": ...} format.
    """
    response = await async_client.get("/api/observability/metrics/aiops")
    assert response.status_code == 200
    data = response.json()

    # CRITICAL: Verify "ok" key exists (not "status")
    assert "ok" in data, "Legacy key 'ok' missing from response"
    assert data["ok"] is True
    assert "data" in data


@pytest.mark.asyncio
async def test_observability_schema_contract_snapshot(
    async_client: AsyncClient,
):
    """
    Refactoring Safety Check:
    Ensures that /performance/snapshot returns the legacy {"status": "success", "snapshot": ...} format.
    """
    response = await async_client.get("/api/observability/performance/snapshot")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "success"
    # CRITICAL: Verify "snapshot" key exists (not just "data")
    assert "snapshot" in data, "Legacy key 'snapshot' missing from response"

    snapshot = data["snapshot"]
    assert "p99_latency_ms" in snapshot


@pytest.mark.asyncio
async def test_observability_schema_contract_alerts(
    async_client: AsyncClient,
):
    """
    Refactoring Safety Check:
    Ensures that /alerts returns the legacy {"status": "success", "alerts": ...} format.
    """
    response = await async_client.get("/api/observability/alerts")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "success"
    # CRITICAL: Verify "alerts" key exists (not just "data")
    assert "alerts" in data, "Legacy key 'alerts' missing from response"
    assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
async def test_observability_health_check_contract(
    async_client: AsyncClient,
):
    """
    Refactoring Safety Check:
    Ensures that the Health Check endpoint returns the correct structure.
    """
    response = await async_client.get("/api/observability/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["status"] == "healthy"
