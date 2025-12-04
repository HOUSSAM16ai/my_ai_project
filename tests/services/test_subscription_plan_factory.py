from decimal import Decimal

import pytest

from app.services.api_subscription_service import SubscriptionPlan, SubscriptionTier
from app.services.subscription_plan_factory import SubscriptionPlanFactory


class TestSubscriptionPlanFactory:
    """Test suite for SubscriptionPlanFactory"""

    def test_create_plan_success(self):
        """Test creating plans for all valid keys"""
        valid_keys = ["free", "starter", "pro", "business", "enterprise"]

        for key in valid_keys:
            plan = SubscriptionPlanFactory.create_plan(key)
            assert isinstance(plan, SubscriptionPlan)
            # Verify the plan ID matches the config
            assert plan.plan_id == SubscriptionPlanFactory.PLAN_CONFIGS[key]["plan_id"]
            # Verify tier is correct
            assert plan.tier == SubscriptionPlanFactory.PLAN_CONFIGS[key]["tier"]

    def test_create_plan_unknown_key(self):
        """Test creating a plan with an unknown key raises KeyError"""
        with pytest.raises(KeyError) as exc_info:
            SubscriptionPlanFactory.create_plan("non_existent_plan")
        assert "Unknown plan key: non_existent_plan" in str(exc_info.value)

    def test_create_all_plans(self):
        """Test creating all plans at once"""
        plans = SubscriptionPlanFactory.create_all_plans()

        assert len(plans) == len(SubscriptionPlanFactory.PLAN_CONFIGS)
        assert set(plans.keys()) == set(SubscriptionPlanFactory.PLAN_CONFIGS.keys())

        for key, plan in plans.items():
            assert isinstance(plan, SubscriptionPlan)
            assert plan.plan_id == SubscriptionPlanFactory.PLAN_CONFIGS[key]["plan_id"]

    def test_get_plan_names(self):
        """Test retrieving all plan names"""
        names = SubscriptionPlanFactory.get_plan_names()
        expected_names = list(SubscriptionPlanFactory.PLAN_CONFIGS.keys())

        assert len(names) == len(expected_names)
        assert sorted(names) == sorted(expected_names)

    def test_decimal_conversion(self):
        """Test that string price fields are correctly converted to Decimal"""
        plan = SubscriptionPlanFactory.create_plan("starter")

        # Check specific Decimal fields
        assert isinstance(plan.base_price, Decimal)
        assert plan.base_price == Decimal("49.00")

        assert isinstance(plan.price_per_1k_calls, Decimal)
        assert plan.price_per_1k_calls == Decimal("0.05")

        assert isinstance(plan.price_per_1m_tokens, Decimal)
        assert plan.price_per_1m_tokens == Decimal("1.00")

        assert isinstance(plan.price_per_compute_hour, Decimal)
        assert plan.price_per_compute_hour == Decimal("0.50")

    def test_free_plan_specifics(self):
        """Test specific attributes of the Free plan"""
        plan = SubscriptionPlanFactory.create_plan("free")

        assert plan.tier == SubscriptionTier.FREE
        assert plan.base_price == Decimal("0.00")
        assert plan.requests_per_minute == 10
        assert plan.overage_allowed is False
        assert plan.is_public is True  # Default value check

    def test_enterprise_plan_specifics(self):
        """Test specific attributes of the Enterprise plan"""
        plan = SubscriptionPlanFactory.create_plan("enterprise")

        assert plan.tier == SubscriptionTier.ENTERPRISE
        assert plan.is_public is False
        assert plan.custom_contract_required is True
        assert plan.features is not None
        assert "White-glove onboarding" in plan.features
