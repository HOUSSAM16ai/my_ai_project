"""وظائف تسجيل الأدوات والأسماء البديلة في السجل."""

from .core_metrics import _init_tool_stats
from .definitions import DISABLED
from .globals import _ALIAS_INDEX, _CAPABILITIES, _TOOL_REGISTRY


def _validate_tool_names(name: str, aliases: list[str]) -> None:
    """التحقق من أن أسماء الأدوات والأسماء البديلة غير مكررة."""
    if name in _TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' already registered.")
    for alias in aliases:
        if alias in _TOOL_REGISTRY or alias in _ALIAS_INDEX:
            raise ValueError(f"Alias '{alias}' already registered.")


def _create_tool_metadata(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    is_alias: bool = False,
) -> dict[str, object]:
    """إنشاء معجم بيانات الأداة الوصفية."""
    return {
        "name": name,
        "description": description,
        "parameters": parameters,
        "handler": None,
        "category": category,
        "canonical": name if not is_alias else None,
        "is_alias": is_alias,
        "aliases": aliases if not is_alias else [],
        "disabled": (allow_disable and name in DISABLED),
    }


def _register_main_tool(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    capabilities: list[str],
) -> None:
    """تسجيل الأداة الرئيسية في السجل."""
    meta = _create_tool_metadata(name, description, parameters, category, aliases, allow_disable)
    meta["canonical"] = name
    _TOOL_REGISTRY[name] = meta
    _CAPABILITIES[name] = capabilities
    _init_tool_stats(name)


def _register_tool_aliases(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    capabilities: list[str],
) -> None:
    """تسجيل الأسماء البديلة للأداة في السجل."""
    for alias in aliases:
        _ALIAS_INDEX[alias] = name
        alias_meta = _create_tool_metadata(
            alias,
            f"[alias of {name}] {description}",
            parameters,
            category,
            [],
            allow_disable,
            is_alias=True,
        )
        alias_meta["canonical"] = name
        _TOOL_REGISTRY[alias] = alias_meta
        _CAPABILITIES[alias] = capabilities
        _init_tool_stats(alias)


def _register_tool_metadata(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    capabilities: list[str],
) -> None:
    """تسجيل الأداة وأسمائها البديلة بعد التحقق من التميز."""
    _validate_tool_names(name, aliases)
    _register_main_tool(
        name, description, parameters, category, aliases, allow_disable, capabilities
    )
    _register_tool_aliases(
        name, description, parameters, category, aliases, allow_disable, capabilities
    )
