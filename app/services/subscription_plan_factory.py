# ======================================================================================
# ==                 SUBSCRIPTION PLAN FACTORY (v1.0)                               ==
# ======================================================================================
# PRIME DIRECTIVE:
#   مصنع خطط الاشتراك - Subscription plan factory pattern
#   ✨ Features:
#   - Data-driven plan creation
#   - Single source of truth for plan definitions
#   - Easy to add/modify plans
#   - Reduces code duplication
#
"""
Subscription Plan Factory Module

Provides a clean factory pattern for creating subscription plans.
All plan configurations are defined as data, making it easy to
maintain and modify without touching code logic.
"""

from decimal import Decimal
from typing import Any

from ..api.subscription_routes import (
    BillingCycle,
    SubscriptionPlan,
    SubscriptionTier,
)


class SubscriptionPlanFactory:
    """
    Factory for creating subscription plans from configuration data.
    
    This class follows the Factory pattern to eliminate code duplication
    and make plan configurations data-driven and maintainable.
    """
    
    # Plan configurations as data
    PLAN_CONFIGS = {
        "free": {
            "plan_id": "plan_free_001",
            "tier": SubscriptionTier.FREE,
            "name": "Free",
            "description": "Perfect for testing and small projects",
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
            "burst_allowance": 20,
            "monthly_api_calls": 10000,
            "monthly_tokens": 100000,
            "monthly_compute_hours": 1.0,
            "features": [
                "Basic API access",
                "Community support",
                "Public documentation",
            ],
            "max_team_members": 1,
            "support_level": "community",
            "sla_guarantee": 0.0,
            "base_price": "0.00",
            "overage_allowed": False,
        },
        "starter": {
            "plan_id": "plan_starter_001",
            "tier": SubscriptionTier.STARTER,
            "name": "Starter",
            "description": "For growing projects and startups",
            "requests_per_minute": 100,
            "requests_per_hour": 5000,
            "requests_per_day": 50000,
            "burst_allowance": 150,
            "monthly_api_calls": 500000,
            "monthly_tokens": 5000000,
            "monthly_compute_hours": 50.0,
            "features": [
                "All Free features",
                "Email support",
                "Advanced analytics",
                "99.9% SLA",
                "Webhook notifications",
            ],
            "max_team_members": 5,
            "support_level": "email",
            "sla_guarantee": 99.9,
            "base_price": "49.00",
            "billing_cycle": BillingCycle.MONTHLY,
            "overage_allowed": True,
            "price_per_1k_calls": "0.05",
            "price_per_1m_tokens": "1.00",
            "price_per_compute_hour": "0.50",
            "max_overage_percent": 20.0,
        },
        "pro": {
            "plan_id": "plan_pro_001",
            "tier": SubscriptionTier.PRO,
            "name": "Pro",
            "description": "For production applications",
            "requests_per_minute": 1000,
            "requests_per_hour": 50000,
            "requests_per_day": 500000,
            "burst_allowance": 1500,
            "monthly_api_calls": 5000000,
            "monthly_tokens": 50000000,
            "monthly_compute_hours": 500.0,
            "features": [
                "All Starter features",
                "Priority support",
                "Custom webhooks",
                "Advanced security features",
                "99.95% SLA",
                "Dedicated account manager",
                "Custom integrations",
            ],
            "max_team_members": 20,
            "support_level": "priority",
            "sla_guarantee": 99.95,
            "base_price": "299.00",
            "billing_cycle": BillingCycle.MONTHLY,
            "overage_allowed": True,
            "price_per_1k_calls": "0.03",
            "price_per_1m_tokens": "0.75",
            "price_per_compute_hour": "0.30",
            "max_overage_percent": 50.0,
        },
        "business": {
            "plan_id": "plan_business_001",
            "tier": SubscriptionTier.BUSINESS,
            "name": "Business",
            "description": "For large organizations",
            "requests_per_minute": 5000,
            "requests_per_hour": 250000,
            "requests_per_day": 2500000,
            "burst_allowance": 7500,
            "monthly_api_calls": 50000000,
            "monthly_tokens": 500000000,
            "monthly_compute_hours": 5000.0,
            "features": [
                "All Pro features",
                "Dedicated support team",
                "Custom SLA",
                "Multi-region deployment",
                "99.99% SLA",
                "Security audit support",
                "Private cloud option",
                "Custom contract terms",
            ],
            "max_team_members": 100,
            "support_level": "dedicated",
            "sla_guarantee": 99.99,
            "base_price": "999.00",
            "billing_cycle": BillingCycle.MONTHLY,
            "overage_allowed": True,
            "price_per_1k_calls": "0.02",
            "price_per_1m_tokens": "0.50",
            "price_per_compute_hour": "0.20",
            "max_overage_percent": 100.0,
        },
        "enterprise": {
            "plan_id": "plan_enterprise_001",
            "tier": SubscriptionTier.ENTERPRISE,
            "name": "Enterprise",
            "description": "Unlimited scale for enterprise",
            "requests_per_minute": 50000,
            "requests_per_hour": 2500000,
            "requests_per_day": 25000000,
            "burst_allowance": 75000,
            "monthly_api_calls": 500000000,
            "monthly_tokens": 5000000000,
            "monthly_compute_hours": 50000.0,
            "features": [
                "All Business features",
                "Unlimited team members",
                "Custom infrastructure",
                "On-premise deployment",
                "99.999% SLA",
                "White-glove onboarding",
                "Custom feature development",
                "Legal & compliance support",
            ],
            "max_team_members": 999999,
            "support_level": "dedicated",
            "sla_guarantee": 99.999,
            "base_price": "4999.00",
            "billing_cycle": BillingCycle.MONTHLY,
            "overage_allowed": True,
            "price_per_1k_calls": "0.01",
            "price_per_1m_tokens": "0.25",
            "price_per_compute_hour": "0.10",
            "max_overage_percent": 200.0,
            "is_public": False,
            "custom_contract_required": True,
        },
    }
    
    @classmethod
    def create_plan(cls, plan_key: str) -> SubscriptionPlan:
        """
        Create a subscription plan from configuration.
        
        Args:
            plan_key: Key identifying the plan (free, starter, pro, etc.)
            
        Returns:
            Configured SubscriptionPlan instance
            
        Raises:
            KeyError: If plan_key is not found in PLAN_CONFIGS
        """
        if plan_key not in cls.PLAN_CONFIGS:
            raise KeyError(f"Unknown plan key: {plan_key}")
        
        config = cls.PLAN_CONFIGS[plan_key].copy()
        
        # Convert string prices to Decimal
        price_fields = [
            "base_price",
            "price_per_1k_calls",
            "price_per_1m_tokens",
            "price_per_compute_hour",
        ]
        
        for field in price_fields:
            if field in config and isinstance(config[field], str):
                config[field] = Decimal(config[field])
        
        return SubscriptionPlan(**config)
    
    @classmethod
    def create_all_plans(cls) -> dict[str, SubscriptionPlan]:
        """
        Create all default subscription plans.
        
        Returns:
            Dictionary mapping plan keys to SubscriptionPlan instances
        """
        return {key: cls.create_plan(key) for key in cls.PLAN_CONFIGS}
    
    @classmethod
    def get_plan_names(cls) -> list[str]:
        """
        Get list of all available plan names.
        
        Returns:
            List of plan keys
        """
        return list(cls.PLAN_CONFIGS.keys())
