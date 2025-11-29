import pytest
from app.services.api_gateway_service import PolicyEngine, PolicyRule

class TestPolicyEngineBug:
    def test_default_auth_policy_enforcement(self):
        engine = PolicyEngine()

        # Add the default policy as defined in APIGatewayService._initialize_default_policies
        engine.add_policy(
            PolicyRule(
                rule_id="require_auth",
                name="Require Authentication",
                condition="auth_required and not authenticated",
                action="deny",
                priority=100,
                enabled=True,
            )
        )

        # Case 1: Unauthenticated request
        context_unauth = {
            "user_id": None,
            "endpoint": "/protected",
            "method": "GET",
            "authenticated": False,
        }

        # This should fail if the bug is present
        allowed, reason = engine.evaluate(context_unauth)
        assert allowed is False, "Unauthenticated request should be denied by default policy"
        assert reason == "Policy violation: Require Authentication"

    def test_authenticated_request_allowed(self):
        engine = PolicyEngine()

        engine.add_policy(
            PolicyRule(
                rule_id="require_auth",
                name="Require Authentication",
                condition="auth_required and not authenticated",
                action="deny",
                priority=100,
                enabled=True,
            )
        )

        # Case 2: Authenticated request
        context_auth = {
            "user_id": "user123",
            "endpoint": "/protected",
            "method": "GET",
            "authenticated": True,
        }

        allowed, reason = engine.evaluate(context_auth)
        assert allowed is True
        assert reason is None
