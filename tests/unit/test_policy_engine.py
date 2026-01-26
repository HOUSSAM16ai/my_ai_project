from app.core.gateway.models import PolicyRule
from app.core.gateway.policy import PolicyEngine


def test_add_policy_updates_registry() -> None:
    engine = PolicyEngine()
    rule = PolicyRule(
        rule_id="auth_required",
        name="Auth required",
        condition="not authenticated",
        action="deny",
        priority=10,
    )

    engine.add_policy(rule)

    assert engine.policies["auth_required"] == rule


def test_evaluate_skips_disabled_policy() -> None:
    engine = PolicyEngine()
    rule = PolicyRule(
        rule_id="disabled",
        name="Disabled policy",
        condition="not authenticated",
        action="deny",
        enabled=False,
    )
    engine.add_policy(rule)

    allowed, reason = engine.evaluate({"authenticated": False})

    assert allowed is True
    assert reason is None


def test_evaluate_denies_when_condition_matches() -> None:
    engine = PolicyEngine()
    rule = PolicyRule(
        rule_id="auth_required",
        name="Auth required",
        condition="not authenticated",
        action="deny",
        priority=100,
    )
    engine.add_policy(rule)

    allowed, reason = engine.evaluate({"authenticated": False})

    assert allowed is False
    assert "Auth required" in reason
    assert engine.violations


def test_evaluate_allows_when_condition_not_met() -> None:
    engine = PolicyEngine()
    rule = PolicyRule(
        rule_id="auth_required",
        name="Auth required",
        condition="not authenticated",
        action="deny",
    )
    engine.add_policy(rule)

    allowed, reason = engine.evaluate({"authenticated": True})

    assert allowed is True
    assert reason is None
    assert engine.violations == []


def test_user_id_requirement_condition() -> None:
    engine = PolicyEngine()
    rule = PolicyRule(
        rule_id="user_required",
        name="User required",
        condition="user_id required",
        action="deny",
    )
    engine.add_policy(rule)

    denied, _ = engine.evaluate({})
    allowed, _ = engine.evaluate({"user_id": "123"})

    assert denied is False
    assert allowed is True
