
import pytest

from app.services.api_subscription_service import (
    APISubscriptionService,
    SubscriptionStatus,
    SubscriptionTier,
    UsageMetricType,
)


class TestAPISubscriptionServiceComprehensive:
    @pytest.fixture
    def service(self):
        # Reset the singleton if necessary or create a new instance
        # Since the singleton pattern is used, we might need to be careful.
        # However, the class `APISubscriptionService` can be instantiated directly for testing
        # if we ignore the `get_subscription_service` helper, or we can mock it.
        # Let's instantiate directly to have a fresh state.
        svc = APISubscriptionService()
        return svc

    def test_create_subscription_success(self, service):
        """Test creating a valid subscription."""
        # Use a known plan from the factory default
        sub = service.create_subscription("cust_123", "starter")

        assert sub is not None
        assert sub.customer_id == "cust_123"
        assert sub.plan.tier == SubscriptionTier.STARTER
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.quota_remaining["api_calls"] == 500000  # From factory config

    def test_create_subscription_invalid_plan(self, service):
        """Test creating subscription with invalid plan ID."""
        sub = service.create_subscription("cust_123", "invalid_plan_id")
        assert sub is None

    def test_create_subscription_with_trial(self, service):
        """Test creating a subscription with a trial period."""
        sub = service.create_subscription("cust_123", "pro", trial_days=14)

        assert sub is not None
        assert sub.status == SubscriptionStatus.TRIAL
        assert sub.trial_end is not None
        assert sub.trial_end > sub.created_at

    def test_record_usage_success(self, service):
        """Test recording usage correctly updates metrics."""
        sub = service.create_subscription("cust_123", "free")
        sub_id = sub.subscription_id

        # Free plan has 10,000 monthly calls
        initial_quota = sub.quota_remaining["api_calls"]

        success = service.record_usage(sub_id, UsageMetricType.API_CALLS, 100)

        assert success is True
        assert sub.current_usage["api_calls"] == 100
        assert sub.quota_remaining["api_calls"] == initial_quota - 100
        assert sub.lifetime_requests == 100

    def test_record_usage_quota_exceeded_no_overage(self, service):
        """Test blocking usage when quota is exceeded and overage not allowed."""
        # Free plan: overage_allowed = False
        sub = service.create_subscription("cust_123", "free")
        sub_id = sub.subscription_id

        # Set quota to 0 manually
        sub.quota_remaining["api_calls"] = 0

        success = service.record_usage(sub_id, UsageMetricType.API_CALLS, 1)

        assert success is False
        # Usage should not increase
        assert sub.current_usage["api_calls"] == 0

    def test_record_usage_quota_exceeded_overage_allowed(self, service):
        """Test allowing usage when quota exceeded but overage is allowed."""
        # Starter plan: overage_allowed = True
        sub = service.create_subscription("cust_123", "starter")
        sub_id = sub.subscription_id

        # Set quota to 0
        sub.quota_remaining["api_calls"] = 0

        success = service.record_usage(sub_id, UsageMetricType.API_CALLS, 100)

        assert success is True
        # Quota becomes negative
        assert sub.quota_remaining["api_calls"] == -100
        assert sub.current_usage["api_calls"] == 100

    def test_upgrade_subscription_success(self, service):
        """Test upgrading from lower to higher tier."""
        sub = service.create_subscription("cust_123", "free")
        sub_id = sub.subscription_id

        # Upgrade Free -> Pro
        success = service.upgrade_subscription(sub_id, "pro")

        assert success is True
        assert sub.plan.tier == SubscriptionTier.PRO
        assert sub.plan.name == "Pro"

    def test_upgrade_subscription_fail_downgrade(self, service):
        """Test that upgrade_subscription fails if trying to downgrade (logic check)."""
        # Note: The method is named 'upgrade_subscription' and explicitly checks for upgrades.
        # Downgrades might be handled differently or just return False here.
        sub = service.create_subscription("cust_123", "pro")
        sub_id = sub.subscription_id

        # Attempt Pro -> Free
        success = service.upgrade_subscription(sub_id, "free")

        assert success is False
        assert sub.plan.tier == SubscriptionTier.PRO

    def test_get_usage_analytics(self, service):
        """Test analytics retrieval."""
        sub = service.create_subscription("cust_123", "starter")
        sub_id = sub.subscription_id

        service.record_usage(sub_id, UsageMetricType.API_CALLS, 500)

        analytics = service.get_usage_analytics(sub_id)

        assert analytics["subscription_id"] == sub_id
        assert analytics["usage"]["api_calls"] == 500
        assert analytics["plan"] == "Starter"
        # 500 / 500,000 * 100 = 0.1%
        assert analytics["usage_percent"]["api_calls"] == 0.1

    def test_get_revenue_metrics(self, service):
        """Test aggregated revenue metrics."""
        # Add a few subscriptions
        # Starter: $49
        service.create_subscription("cust_1", "starter")
        # Pro: $299
        service.create_subscription("cust_2", "pro")
        # Free: $0
        service.create_subscription("cust_3", "free")

        metrics = service.get_revenue_metrics()

        expected_mrr = 49 + 299 + 0
        assert metrics["active_subscriptions"] == 3
        assert metrics["mrr"] == float(expected_mrr)
        assert metrics["arr"] == float(expected_mrr * 12)
        assert metrics["average_revenue_per_user"] == float(expected_mrr / 3)
