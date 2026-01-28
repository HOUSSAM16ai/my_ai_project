import pytest

from app.services.search_engine import query_refiner


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2024", 2024),
        (2025, 2025),
        ("none", None),
        (None, None),
        ("invalid", None),
    ],
)
def test_safe_int_handles_common_inputs(value, expected):
    assert query_refiner._safe_int(value) == expected


def test_get_refined_query_falls_back_on_failure(monkeypatch):
    def _raise_error(*args, **kwargs):
        raise RuntimeError("DSPy unavailable")

    monkeypatch.setattr(query_refiner.dspy, "LM", _raise_error)

    result = query_refiner.get_refined_query("اختبار", api_key="token")

    assert result == {
        "refined_query": "اختبار",
        "year": None,
        "subject": None,
        "branch": None,
    }
