"""اختبارات إدارة إعدادات الوسطاء."""

from app.middleware.config.middleware_settings import ConfigValue, MiddlewareSettings


def test_initialization_and_get_set_roundtrip() -> None:
    settings = MiddlewareSettings()

    assert settings.get("missing") is None

    settings.set("timeout", 30)
    settings.set("features", ["logging", "tracing"])

    assert settings.get("timeout") == 30
    assert settings.get("features") == ["logging", "tracing"]


def test_from_items_and_to_dict_are_defensive() -> None:
    items: list[tuple[str, ConfigValue]] = [
        ("mode", "dev"),
        ("limits", {"requests": [1, 2, 3]}),
    ]

    settings = MiddlewareSettings.from_items(items)

    exported = settings.to_dict()
    assert exported == {"mode": "dev", "limits": {"requests": [1, 2, 3]}}

    items.append(("new", "value"))
    exported["mode"] = "prod"

    assert settings.get("mode") == "dev"
    assert settings.get("new") is None
