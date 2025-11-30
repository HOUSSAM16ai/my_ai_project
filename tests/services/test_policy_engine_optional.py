from app.services.api_gateway_service import PolicyEngine, PolicyRule


def test_policy_engine_optional_user_id_bug():
    """
    Verifies that a policy with condition "user_id optional" does NOT interpret
    it as "user_id required".

    Current Bug: The simplistic string matching in _evaluate_condition checks if "user_id" is present
    and "not required" is NOT present. It fails to account for other qualifiers like "optional".
    """
    engine = PolicyEngine()
    policy = PolicyRule(
        rule_id="optional_user",
        name="Optional User ID",
        condition="user_id optional",
        action="deny",
        priority=100,
        enabled=True,
    )
    engine.add_policy(policy)

    context = {
        "user_id": None,
        "endpoint": "/public/resource",
        "method": "GET",
        "authenticated": False,
    }

    allowed, reason = engine.evaluate(context)

    # We expect allowed=True because it's optional.
    # The bug will cause allowed=False because it matches "user_id" and doesn't see "not required".
    assert allowed is True, f"Policy erroneously denied request with reason: {reason}"
