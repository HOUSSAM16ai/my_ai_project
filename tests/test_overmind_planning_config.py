from app.services.overmind.planning.config import (
    DEFAULT_CONFIG,
    _parse_bool,
    _parse_csv,
    _parse_float,
    _parse_int,
)


def test_default_config_values():
    assert DEFAULT_CONFIG.min_reliability == 0.25
    assert DEFAULT_CONFIG.deep_fingerprint is True
    # Check for actual planner names (not module names)
    assert "ultra_hyper_semantic_planner" in DEFAULT_CONFIG.allowed_planners


def test_parse_csv():
    assert _parse_csv("a,b,c") == {"a", "b", "c"}
    assert _parse_csv(" a ,b, c ") == {"a", "b", "c"}
    assert _parse_csv("") == set()


def test_parse_bool():
    assert _parse_bool("1") is True
    assert _parse_bool("true") is True
    assert _parse_bool("yes") is True
    assert _parse_bool("on") is True
    assert _parse_bool("0") is False
    assert _parse_bool("false") is False
    assert _parse_bool("") is False
    assert _parse_bool("any other string") is False


def test_parse_float():
    assert _parse_float("1.23", 0.0) == 1.23
    assert _parse_float(None, 5.0) == 5.0
    assert _parse_float("abc", 5.0) == 5.0


def test_parse_int():
    assert _parse_int("123", 0) == 123
    assert _parse_int(None, 5) == 5
    assert _parse_int("abc", 5) == 5
