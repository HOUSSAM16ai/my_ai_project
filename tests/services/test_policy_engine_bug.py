from app.services.api_gateway_service import PolicyEngine, PolicyRule


class TestPolicyEngineBug:
    def test_user_id_policy_enforcement(self):
        engine = PolicyEngine()

        # Add a policy that checks for user_id presence
        # The condition logic in _evaluate_condition checks:
        # bool("user_id" in condition and "user_id" not in context)
        policy = PolicyRule(
            rule_id="check_user_id",
            name="Check User ID",
            condition="user_id required",
            action="deny",
            priority=100,
            enabled=True,
        )
        engine.add_policy(policy)

        # Context where user_id key exists but value is None (typical FastAPI request state)
        context = {
            "user_id": None,
            "endpoint": "/api/test",
            "method": "GET",
            "authenticated": False,
        }

        allowed, reason = engine.evaluate(context)

        # This assertion expects the bug to be fixed (i.e., request denied)
        # So it should FAIL currently.
        assert allowed is False, "Policy should deny request when user_id is None"
        assert reason == "Policy violation: Check User ID"

    def test_authenticated_request_allowed(self):
        engine = PolicyEngine()
        policy = PolicyRule(
            rule_id="check_user_id",
            name="Check User ID",
            condition="user_id required",
            action="deny",
            priority=100,
            enabled=True,
        )
        engine.add_policy(policy)

        context = {
            "user_id": "123",
            "endpoint": "/api/test",
            "method": "GET",
            "authenticated": True,
        }

        allowed, reason = engine.evaluate(context)
        assert allowed is True
        assert reason is None

    def test_false_positive_user_id_check(self):
        """
        Ensure that a policy condition containing 'user_id' as a substring
        (without 'required' keyword) does NOT trigger the mandatory user_id check.
        """
        engine = PolicyEngine()
        policy = PolicyRule(
            rule_id="feature_flag_check",
            name="Check Feature Flag",
            condition="check_feature_flag_user_id_segment",
            action="deny",
            priority=100,
            enabled=True,
        )
        engine.add_policy(policy)

        # Anonymous context
        context = {
            "user_id": None,
            "endpoint": "/public/feature",
            "method": "GET",
            "authenticated": False,
        }

        allowed, reason = engine.evaluate(context)

        # Should be allowed because 'required' is missing from condition
        assert allowed is True, f"Policy erroneously denied request: {reason}"
