import pytest
from app.services.api_gateway_service import PolicyEngine, PolicyRule

class TestPolicyEngineSemantics:
    def test_confusing_policy_condition(self):
        """
        Demonstrate that 'user_id not required' is interpreted as 'user_id required'
        due to simplistic string matching.
        """
        engine = PolicyEngine()

        # User intends to explicitly ALLOW missing user_id, or just have a descriptive condition
        # that happens to contain the string "user_id".
        policy = PolicyRule(
            rule_id="loose_check",
            name="Loose Check",
            condition="user_id not required",
            action="deny",
            priority=100,
            enabled=True
        )
        engine.add_policy(policy)

        # Context where user_id is missing
        context = {
            "user_id": None,
            "endpoint": "/public/resource",
            "method": "GET",
            "authenticated": False
        }

        # Expectation: This policy should NOT deny the request, because the condition
        # "user_id not required" implies we don't care about user_id.
        # But current implementation checks 'if "user_id" in condition' and then enforces presence.

        allowed, reason = engine.evaluate(context)

        # We assert True, expecting it to FAIL initially because the code is buggy
        assert allowed is True, f"Policy erroneously denied request with reason: {reason}"
        assert reason is None
