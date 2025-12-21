# app.services.overmind/planning/config.py
# ======================================================================================
# PLANNER FACTORY CONFIGURATION
# Version 5.0.0 - Typed Configuration Management
# ======================================================================================
"""
Configuration management for the Planner Factory.
Centralizes all environment-based configuration with type safety.
"""

import os
from dataclasses import dataclass
from typing import Any


def _parse_csv(s: str) -> set[str]:
    """Parse comma-separated string into a set."""
    return {p.strip() for p in s.split(",") if p.strip()}


def _parse_bool(s: str, default: bool = False) -> bool:
    """Parse string to boolean."""
    if not s:
        return default
    return s.lower() in ("1", "true", "yes", "on")


def _parse_float(s: str | None, default: float) -> float:
    """Parse string to float with fallback."""
    if not s:
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def _parse_int(s: str | None, default: int) -> int:
    """Parse string to int with fallback."""
    if not s:
        return default
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


@dataclass
class FactoryConfig:
    """Typed configuration for PlannerFactory with environment-based defaults."""

    # Planner filtering and discovery
    allowed_planners: set[str]
    exclude_modules: set[str]
    manual_modules: list[str]

    # Discovery behavior
    force_rediscover: bool
    deep_fingerprint: bool

    # Filtering thresholds
    min_reliability: float
    default_reliability: float

    # Self-healing
    self_heal_on_empty: bool
    self_heal_blocking: bool

    # Profiling
    profile_selection: bool
    profile_instantiation: bool
    max_profiles: int

    # Deep context boosting
    deep_index_cap_boost: float
    hotspot_cap_boost: float
    hotspot_threshold: int

    # Logging
    log_level: str

    @classmethod
    def from_env(cls) -> "FactoryConfig":
        """Create configuration from environment variables."""
        # Default modules to exclude
        default_exclude = {
            "__init__",
            "factory",
            "factory_core",
            "base_planner",
            "schemas",
            "deep_indexer",
            "sandbox",
            "config",
            "ranking",
            "telemetry",
            "exceptions",
        }

        # Parse allowed planners
        # NOTE: These names must match the 'name' class attribute of each planner,
        # NOT the module filename. UltraHyperPlanner uses 'ultra_hyper_semantic_planner',
        # and AdaptiveMultiPassArchPlanner uses 'adaptive_multi_pass_arch_planner'.
        allowed_str = os.getenv(
            "FACTORY_ALLOWED_PLANNERS",
            "ultra_hyper_semantic_planner,risk_planner,structural_planner,adaptive_multi_pass_arch_planner",
        )
        allowed_planners = _parse_csv(allowed_str)

        # Parse manual modules
        manual_str = os.getenv("OVERMIND_PLANNER_MANUAL", "")
        manual_modules = [m.strip() for m in manual_str.split(",") if m.strip()]

        # Add official manual modules
        official_manual = [
            "app.services.overmind.planning.llm_planner",
            "app.services.overmind.planning.multi_pass_arch_planner",
        ]
        manual_modules = list(dict.fromkeys(official_manual + manual_modules))

        # Parse exclude modules
        exclude_str = os.getenv("OVERMIND_PLANNER_EXCLUDE", "")
        env_exclude = _parse_csv(exclude_str)
        exclude_modules = default_exclude | env_exclude

        return cls(
            allowed_planners=allowed_planners,
            exclude_modules=exclude_modules,
            manual_modules=manual_modules,
            force_rediscover=_parse_bool(os.getenv("FACTORY_FORCE_REDISCOVER", "0")),
            deep_fingerprint=_parse_bool(os.getenv("FACTORY_DEEP_FINGERPRINT", "1"), True),
            min_reliability=_parse_float(os.getenv("FACTORY_MIN_RELIABILITY"), 0.25),
            default_reliability=0.1,  # Strict default (was 0.5 in older versions)
            self_heal_on_empty=_parse_bool(os.getenv("FACTORY_SELF_HEAL_ON_EMPTY", "0")),
            self_heal_blocking=_parse_bool(os.getenv("FACTORY_SELF_HEAL_BLOCKING", "1"), True),
            profile_selection=_parse_bool(os.getenv("FACTORY_PROFILE_SELECTION", "1"), True),
            profile_instantiation=_parse_bool(
                os.getenv("FACTORY_PROFILE_INSTANTIATION", "1"), True
            ),
            max_profiles=_parse_int(os.getenv("FACTORY_MAX_PROFILES"), 1000),
            deep_index_cap_boost=_parse_float(os.getenv("FACTORY_DEEP_INDEX_CAP_BOOST"), 0.05),
            hotspot_cap_boost=_parse_float(os.getenv("FACTORY_HOTSPOT_CAP_BOOST"), 0.03),
            hotspot_threshold=_parse_int(os.getenv("FACTORY_HOTSPOT_THRESHOLD"), 8),
            log_level=os.getenv("FACTORY_LOG_LEVEL", "INFO"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "allowed_planners": sorted(self.allowed_planners),
            "exclude_modules": sorted(self.exclude_modules),
            "manual_modules": self.manual_modules,
            "force_rediscover": self.force_rediscover,
            "deep_fingerprint": self.deep_fingerprint,
            "min_reliability": self.min_reliability,
            "default_reliability": self.default_reliability,
            "self_heal_on_empty": self.self_heal_on_empty,
            "self_heal_blocking": self.self_heal_blocking,
            "profile_selection": self.profile_selection,
            "profile_instantiation": self.profile_instantiation,
            "max_profiles": self.max_profiles,
            "deep_index_cap_boost": self.deep_index_cap_boost,
            "hotspot_cap_boost": self.hotspot_cap_boost,
            "hotspot_threshold": self.hotspot_threshold,
            "log_level": self.log_level,
        }


# Global default configuration (can be overridden by PlannerFactory instances)
DEFAULT_CONFIG = FactoryConfig.from_env()


__all__ = [
    "DEFAULT_CONFIG",
    "FactoryConfig",
]
