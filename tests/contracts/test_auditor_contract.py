import json
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.clients.auditor_client import AuditorClient
from microservices.auditor_service.src.schemas import (
    ConsultRequest,
    ReviewRequest,
    ReviewResponse,
)


# Mock Context
class MockContext:
    def __init__(self, data):
        self.shared_memory = data

    def update(self, k, v):
        self.shared_memory[k] = v

    def get(self, k):
        return self.shared_memory.get(k)


@pytest.mark.asyncio
async def test_auditor_client_complies_with_contract():
    """
    Consumer-Driven Contract Test:
    Verifies that AuditorClient generates requests that match the Microservice Schema.
    """
    client = AuditorClient()

    # Test Data
    result_data = {"execution": "success", "steps": []}
    objective = "Fix the bug"
    context_data = {"env": "prod"}
    context = MockContext(context_data)

    # Mock httpx to capture the request payload
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Prepare successful response matching the contract
        expected_response = {
            "approved": True,
            "feedback": "Good job",
            "score": 0.95,
            "final_response": "Completed successfully",
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = expected_response

        # Action
        response = await client.review_work(result_data, objective, context)

        # Verify Response
        assert response == expected_response

        # Verify Request Payload (The Contract Check)
        call_args = mock_post.call_args
        url = call_args[0][0]
        json_payload = call_args.kwargs["json"]

        # 1. Check URL
        assert "/review" in url

        # 2. Validate Payload against Schema (Contract)
        try:
            ReviewRequest(**json_payload)
        except Exception as e:
            pytest.fail(f"Client generated invalid payload according to contract: {e}")


@pytest.mark.asyncio
async def test_auditor_service_implements_contract():
    """
    Provider Contract Test:
    Verifies that AuditorService accepts valid requests and returns valid responses.
    """
    from microservices.auditor_service.src.core import AuditorService

    # Mock AI Client to avoid external calls
    with patch(
        "microservices.auditor_service.src.core.SimpleAIClient.send_message", new_callable=AsyncMock
    ) as mock_ai:
        # Mock LLM returning valid JSON matching schema
        mock_ai.return_value = json.dumps(
            {"approved": True, "feedback": "Excellent", "score": 1.0, "final_response": "Perfect."}
        )

        service = AuditorService()

        request_payload = {
            "result": {"status": "done"},
            "original_objective": "Test",
            "context": {},
        }

        # Create Request Object (Contract)
        request = ReviewRequest(**request_payload)

        # Action
        response = await service.review_work(request)

        # Verify Response matches Contract
        assert isinstance(response, ReviewResponse)
        assert response.approved is True
        assert response.score == 1.0


@pytest.mark.asyncio
async def test_auditor_consult_contract():
    """
    Test Consultation Contract.
    """
    client = AuditorClient()
    situation = "System overload"
    analysis = {"load": 99}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        expected_resp = {"recommendation": "Scale up", "confidence": 90.0}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = expected_resp

        await client.consult(situation, analysis)

        # Verify Payload
        json_payload = mock_post.call_args.kwargs["json"]
        try:
            ConsultRequest(**json_payload)
        except Exception as e:
            pytest.fail(f"Client generated invalid Consult payload: {e}")
