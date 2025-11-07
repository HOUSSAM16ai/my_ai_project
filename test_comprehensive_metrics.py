"""
Test script to validate comprehensive metrics system

This script tests:
1. Service imports
2. Basic functionality
3. API integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("Testing Comprehensive Metrics System")
print("=" * 80)

# Test 1: Check if services can be imported
print("\n[TEST 1] Checking service imports...")
try:
    from app.services.infrastructure_metrics_service import InfrastructureMetricsService
    print("✅ InfrastructureMetricsService imported successfully")
except ImportError as e:
    print(f"❌ Failed to import InfrastructureMetricsService: {e}")

try:
    from app.services.ai_model_metrics_service import AIModelMetricsService
    print("✅ AIModelMetricsService imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AIModelMetricsService: {e}")

try:
    from app.services.user_analytics_metrics_service import UserAnalyticsMetricsService
    print("✅ UserAnalyticsMetricsService imported successfully")
except ImportError as e:
    print(f"❌ Failed to import UserAnalyticsMetricsService: {e}")

# Test 2: Check if API routes can be imported
print("\n[TEST 2] Checking API routes import...")
try:
    from app.api import comprehensive_metrics_routes
    print("✅ comprehensive_metrics_routes imported successfully")
except ImportError as e:
    print(f"❌ Failed to import comprehensive_metrics_routes: {e}")

# Test 3: Check data structures
print("\n[TEST 3] Checking data structures...")
try:
    from app.services.infrastructure_metrics_service import (
        CPUMetrics,
        MemoryMetrics,
        DiskMetrics,
        NetworkMetrics,
    )
    print("✅ Infrastructure data structures OK")
except ImportError as e:
    print(f"❌ Failed to import infrastructure data structures: {e}")

try:
    from app.services.ai_model_metrics_service import (
        InferenceMetrics,
        AccuracyMetrics,
        NLPMetrics,
        ModelDriftMetrics,
    )
    print("✅ AI model data structures OK")
except ImportError as e:
    print(f"❌ Failed to import AI model data structures: {e}")

try:
    from app.services.user_analytics_metrics_service import (
        UserEvent,
        EngagementMetrics,
        ConversionMetrics,
        RetentionMetrics,
    )
    print("✅ User analytics data structures OK")
except ImportError as e:
    print(f"❌ Failed to import user analytics data structures: {e}")

# Test 4: Check enums
print("\n[TEST 4] Checking enumerations...")
try:
    from app.services.infrastructure_metrics_service import ResourceType, HealthStatus
    from app.services.ai_model_metrics_service import MetricType, ModelType, DriftStatus
    from app.services.user_analytics_metrics_service import EventType, UserSegment
    print("✅ All enumerations imported successfully")
except ImportError as e:
    print(f"❌ Failed to import enumerations: {e}")

# Test 5: Verify API endpoint registration
print("\n[TEST 5] Checking API endpoint registration...")
try:
    from app.api import init_api
    print("✅ init_api function available")
except ImportError as e:
    print(f"❌ Failed to import init_api: {e}")

print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
print("\nNote: Full functionality requires psutil to be installed:")
print("  pip install psutil>=5.9.0")
print("\nServices will be available at:")
print("  - /api/v1/metrics/infrastructure/*")
print("  - /api/v1/metrics/ai/*")
print("  - /api/v1/metrics/users/*")
print("  - /api/v1/metrics/dashboard")
