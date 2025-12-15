# app/services/ai_intelligent_testing.py
# ======================================================================================
# ==        SUPERHUMAN AI-POWERED INTELLIGENT TESTING SYSTEM (v1.0)                 ==
# ======================================================================================
# SHIM FILE FOR BACKWARD COMPATIBILITY
# This service has been refactored into a modular structure at app/services/ai_testing/

from app.services.ai_testing.domain.models import (
    TestType,
    CoverageType,
    TestCase,
    CodeAnalysis,
)
from app.services.ai_testing.generators.test_generator import AITestGenerator
from app.services.ai_testing.selectors.smart_selector import SmartTestSelector
from app.services.ai_testing.optimizers.coverage_optimizer import CoverageOptimizer
from app.services.ai_testing.application.manager import IntelligentTestingSystem

# Re-export all public members
__all__ = [
    "TestType",
    "CoverageType",
    "TestCase",
    "CodeAnalysis",
    "AITestGenerator",
    "SmartTestSelector",
    "CoverageOptimizer",
    "IntelligentTestingSystem",  # New unified manager
]

# Note: The original file had a main block for example usage.
# Since this is a library module, we don't strictly need to preserve the __main__ block behavior
# for imports, but we should ensure any global state or classes are available.
# The 'testing_system' instance is available if needed, though the original didn't export a global instance.
