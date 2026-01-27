import math

import pytest

from app.core.gateway.routing import IntelligentRouter


def test_route_request_requires_model_type():
    """Verify routing rejects missing model type."""
    router = IntelligentRouter()

    with pytest.raises(ValueError):
        router.route_request("", estimated_tokens=10)


def test_route_request_rejects_whitespace_model_type():
    """Verify routing rejects whitespace-only model type."""
    router = IntelligentRouter()

    with pytest.raises(ValueError):
        router.route_request("   ", estimated_tokens=10)


def test_route_request_requires_positive_tokens():
    """Verify routing rejects non-positive token estimates."""
    router = IntelligentRouter()

    with pytest.raises(ValueError):
        router.route_request("gpt-4", estimated_tokens=0)


def test_route_request_rejects_negative_constraints():
    """Verify routing rejects negative constraint values."""
    router = IntelligentRouter()

    with pytest.raises(ValueError):
        router.route_request(
            "gpt-4",
            estimated_tokens=10,
            constraints={"max_cost": -1},
        )


def test_route_request_rejects_non_numeric_constraints():
    """Verify routing rejects non-numeric constraint values."""
    router = IntelligentRouter()

    with pytest.raises(ValueError):
        router.route_request(
            "gpt-4",
            estimated_tokens=10,
            constraints={"max_latency": "fast"},
        )


def test_route_request_rejects_nan_constraints():
    """Verify routing rejects NaN constraint values."""
    router = IntelligentRouter()

    with pytest.raises(ValueError):
        router.route_request(
            "gpt-4",
            estimated_tokens=10,
            constraints={"max_cost": float("nan")},
        )


def test_normalize_constraints_allows_none_values():
    """Verify constraint normalization treats None as an absent value."""
    router = IntelligentRouter()

    max_cost, max_latency = router._normalize_constraints({"max_cost": None, "max_latency": None})

    assert math.isinf(max_cost)
    assert math.isinf(max_latency)
