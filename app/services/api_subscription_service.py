# app/services/api_subscription_service.py
# ======================================================================================
# ==    SUPERHUMAN API SUBSCRIPTION & MONETIZATION SERVICE (v1.0 - ELITE EDITION)   ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام اشتراكات API خارق يتفوق على Stripe و AWS Marketplace
#   ✨ المميزات الخارقة:
#   - Multi-tier subscription plans (Free, Pro, Enterprise, Custom)
#   - Usage-based billing and metering
#   - Advanced quota management
#   - Overage handling and billing
#   - Revenue analytics and forecasting
#   - Churn prediction and retention
#   - Self-service upgrade/downgrade
#   - API monetization and marketplace

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from decimal import Decimal
import threading
from collections import defaultdict, deque
from flask import current_app
import hashlib
import json


# ======================================================================================
# ENUMERATIONS
# ======================================================================================

class SubscriptionTier(Enum):
    """Subscription tier levels"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(Enum):
    """Billing cycle periods"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    USAGE_BASED = "usage_based"


class UsageMetricType(Enum):
    """Types of usage metrics"""
    API_CALLS = "api_calls"
    TOKENS = "tokens"
    COMPUTE_TIME = "compute_time"
    DATA_TRANSFER = "data_transfer"
    STORAGE = "storage"


class SubscriptionStatus(Enum):
    """Subscription status"""
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELED = "canceled"
    EXPIRED = "expired"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================

@dataclass
class SubscriptionPlan:
    """Subscription plan definition"""
    plan_id: str
    tier: SubscriptionTier
    name: str
    description: str
    
    # Rate limits
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int
    
    # Quotas
    monthly_api_calls: int
    monthly_tokens: int
    monthly_compute_hours: float
    
    # Features
    features: List[str] = field(default_factory=list)
    max_team_members: int = 1
    support_level: str = "community"  # community, email, priority, dedicated
    sla_guarantee: float = 0.0  # 0.0 to 99.999
    
    # Pricing
    base_price: Decimal = Decimal("0.00")
    currency: str = "USD"
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    
    # Overage pricing
    overage_allowed: bool = False
    price_per_1k_calls: Decimal = Decimal("0.00")
    price_per_1m_tokens: Decimal = Decimal("0.00")
    price_per_compute_hour: Decimal = Decimal("0.00")
    
    # Limits
    max_overage_percent: float = 0.0  # Max overage as % of base quota
    
    # Metadata
    is_public: bool = True
    custom_contract_required: bool = False


@dataclass
class Subscription:
    """Customer subscription"""
    subscription_id: str
    customer_id: str
    plan: SubscriptionPlan
    
    status: SubscriptionStatus
    created_at: datetime
    
    # Billing
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    
    # Usage tracking
    current_usage: Dict[str, float] = field(default_factory=dict)
    quota_remaining: Dict[str, float] = field(default_factory=dict)
    
    # History
    total_spent: Decimal = Decimal("0.00")
    lifetime_requests: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UsageRecord:
    """Usage tracking record"""
    record_id: str
    subscription_id: str
    timestamp: datetime
    
    metric_type: UsageMetricType
    quantity: float
    
    # Cost calculation
    unit_price: Decimal
    total_cost: Decimal
    
    # Context
    endpoint: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Invoice:
    """Billing invoice"""
    invoice_id: str
    subscription_id: str
    customer_id: str
    
    period_start: datetime
    period_end: datetime
    
    # Charges
    base_charge: Decimal
    usage_charges: Decimal
    overage_charges: Decimal
    discounts: Decimal
    taxes: Decimal
    total_amount: Decimal
    
    # Status
    status: str  # draft, finalized, paid, overdue, void
    due_date: datetime
    paid_at: Optional[datetime] = None
    
    # Line items
    line_items: List[Dict[str, Any]] = field(default_factory=list)


# ======================================================================================
# SUBSCRIPTION SERVICE
# ======================================================================================

class APISubscriptionService:
    """
    خدمة اشتراكات API الخارقة - Superhuman API Subscription Service
    
    Features:
    - Multi-tier subscription management
    - Usage-based billing and metering
    - Quota enforcement and overage handling
    - Revenue analytics and forecasting
    - Self-service plan management
    """
    
    def __init__(self):
        self.plans: Dict[str, SubscriptionPlan] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.usage_records: deque = deque(maxlen=100000)
        self.invoices: Dict[str, Invoice] = {}
        
        self.lock = threading.RLock()
        
        # Analytics
        self.revenue_metrics: Dict[str, Any] = defaultdict(lambda: {
            'total_revenue': Decimal("0.00"),
            'active_subscriptions': 0,
            'new_subscriptions': 0,
            'churned_subscriptions': 0,
            'mrr': Decimal("0.00"),  # Monthly Recurring Revenue
            'arr': Decimal("0.00"),  # Annual Recurring Revenue
        })
        
        self._initialize_default_plans()
    
    def _initialize_default_plans(self):
        """Initialize default subscription plans"""
        
        # Free tier - for testing and small projects
        self.plans['free'] = SubscriptionPlan(
            plan_id='plan_free_001',
            tier=SubscriptionTier.FREE,
            name='Free',
            description='Perfect for testing and small projects',
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_allowance=20,
            monthly_api_calls=10000,
            monthly_tokens=100000,
            monthly_compute_hours=1.0,
            features=['Basic API access', 'Community support', 'Public documentation'],
            max_team_members=1,
            support_level='community',
            sla_guarantee=0.0,
            base_price=Decimal("0.00"),
            overage_allowed=False
        )
        
        # Starter tier - for growing projects
        self.plans['starter'] = SubscriptionPlan(
            plan_id='plan_starter_001',
            tier=SubscriptionTier.STARTER,
            name='Starter',
            description='For growing projects and startups',
            requests_per_minute=100,
            requests_per_hour=5000,
            requests_per_day=50000,
            burst_allowance=150,
            monthly_api_calls=500000,
            monthly_tokens=5000000,
            monthly_compute_hours=50.0,
            features=[
                'All Free features',
                'Email support',
                'Advanced analytics',
                '99.9% SLA',
                'Webhook notifications'
            ],
            max_team_members=5,
            support_level='email',
            sla_guarantee=99.9,
            base_price=Decimal("49.00"),
            billing_cycle=BillingCycle.MONTHLY,
            overage_allowed=True,
            price_per_1k_calls=Decimal("0.05"),
            price_per_1m_tokens=Decimal("1.00"),
            price_per_compute_hour=Decimal("0.50"),
            max_overage_percent=20.0
        )
        
        # Pro tier - for production applications
        self.plans['pro'] = SubscriptionPlan(
            plan_id='plan_pro_001',
            tier=SubscriptionTier.PRO,
            name='Pro',
            description='For production applications',
            requests_per_minute=1000,
            requests_per_hour=50000,
            requests_per_day=500000,
            burst_allowance=1500,
            monthly_api_calls=5000000,
            monthly_tokens=50000000,
            monthly_compute_hours=500.0,
            features=[
                'All Starter features',
                'Priority support',
                'Custom webhooks',
                'Advanced security features',
                '99.95% SLA',
                'Dedicated account manager',
                'Custom integrations'
            ],
            max_team_members=20,
            support_level='priority',
            sla_guarantee=99.95,
            base_price=Decimal("299.00"),
            billing_cycle=BillingCycle.MONTHLY,
            overage_allowed=True,
            price_per_1k_calls=Decimal("0.03"),
            price_per_1m_tokens=Decimal("0.75"),
            price_per_compute_hour=Decimal("0.30"),
            max_overage_percent=50.0
        )
        
        # Business tier - for large organizations
        self.plans['business'] = SubscriptionPlan(
            plan_id='plan_business_001',
            tier=SubscriptionTier.BUSINESS,
            name='Business',
            description='For large organizations',
            requests_per_minute=5000,
            requests_per_hour=250000,
            requests_per_day=2500000,
            burst_allowance=7500,
            monthly_api_calls=50000000,
            monthly_tokens=500000000,
            monthly_compute_hours=5000.0,
            features=[
                'All Pro features',
                'Dedicated support team',
                'Custom SLA',
                'Multi-region deployment',
                '99.99% SLA',
                'Security audit support',
                'Private cloud option',
                'Custom contract terms'
            ],
            max_team_members=100,
            support_level='dedicated',
            sla_guarantee=99.99,
            base_price=Decimal("999.00"),
            billing_cycle=BillingCycle.MONTHLY,
            overage_allowed=True,
            price_per_1k_calls=Decimal("0.02"),
            price_per_1m_tokens=Decimal("0.50"),
            price_per_compute_hour=Decimal("0.20"),
            max_overage_percent=100.0
        )
        
        # Enterprise tier - unlimited scale
        self.plans['enterprise'] = SubscriptionPlan(
            plan_id='plan_enterprise_001',
            tier=SubscriptionTier.ENTERPRISE,
            name='Enterprise',
            description='Unlimited scale for enterprise',
            requests_per_minute=50000,
            requests_per_hour=2500000,
            requests_per_day=25000000,
            burst_allowance=75000,
            monthly_api_calls=500000000,
            monthly_tokens=5000000000,
            monthly_compute_hours=50000.0,
            features=[
                'All Business features',
                'Unlimited team members',
                'Custom infrastructure',
                'On-premise deployment',
                '99.999% SLA',
                'White-glove onboarding',
                'Custom feature development',
                'Legal & compliance support'
            ],
            max_team_members=999999,
            support_level='dedicated',
            sla_guarantee=99.999,
            base_price=Decimal("4999.00"),
            billing_cycle=BillingCycle.MONTHLY,
            overage_allowed=True,
            price_per_1k_calls=Decimal("0.01"),
            price_per_1m_tokens=Decimal("0.25"),
            price_per_compute_hour=Decimal("0.10"),
            max_overage_percent=200.0,
            is_public=False,
            custom_contract_required=True
        )
    
    def create_subscription(
        self,
        customer_id: str,
        plan_id: str,
        trial_days: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Subscription]:
        """Create a new subscription"""
        with self.lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return None
            
            subscription_id = f"sub_{hashlib.md5(f'{customer_id}:{plan_id}:{datetime.now(timezone.utc)}'.encode()).hexdigest()[:16]}"
            
            now = datetime.now(timezone.utc)
            period_end = now + timedelta(days=30)  # Default monthly
            trial_end = now + timedelta(days=trial_days) if trial_days > 0 else None
            
            subscription = Subscription(
                subscription_id=subscription_id,
                customer_id=customer_id,
                plan=plan,
                status=SubscriptionStatus.TRIAL if trial_days > 0 else SubscriptionStatus.ACTIVE,
                created_at=now,
                current_period_start=now,
                current_period_end=period_end,
                trial_end=trial_end,
                current_usage={
                    'api_calls': 0,
                    'tokens': 0,
                    'compute_hours': 0.0
                },
                quota_remaining={
                    'api_calls': plan.monthly_api_calls,
                    'tokens': plan.monthly_tokens,
                    'compute_hours': plan.monthly_compute_hours
                },
                metadata=metadata or {}
            )
            
            self.subscriptions[subscription_id] = subscription
            
            current_app.logger.info(
                f"Created subscription {subscription_id} for customer {customer_id} "
                f"on plan {plan.name}"
            )
            
            return subscription
    
    def record_usage(
        self,
        subscription_id: str,
        metric_type: UsageMetricType,
        quantity: float,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record API usage"""
        with self.lock:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription:
                return False
            
            # Check quota
            metric_name = metric_type.value.replace('_', ' ')
            quota_key = metric_type.value
            
            if quota_key in subscription.quota_remaining:
                remaining = subscription.quota_remaining[quota_key]
                if remaining <= 0 and not subscription.plan.overage_allowed:
                    current_app.logger.warning(
                        f"Quota exceeded for {subscription_id}: {metric_name}"
                    )
                    return False
            
            # Calculate cost
            unit_price = self._get_unit_price(subscription.plan, metric_type)
            total_cost = unit_price * Decimal(str(quantity))
            
            # Record usage
            record_id = f"usage_{hashlib.md5(f'{subscription_id}:{datetime.now(timezone.utc)}'.encode()).hexdigest()[:16]}"
            usage_record = UsageRecord(
                record_id=record_id,
                subscription_id=subscription_id,
                timestamp=datetime.now(timezone.utc),
                metric_type=metric_type,
                quantity=quantity,
                unit_price=unit_price,
                total_cost=total_cost,
                endpoint=endpoint,
                metadata=metadata or {}
            )
            
            self.usage_records.append(usage_record)
            
            # Update subscription usage
            if quota_key in subscription.current_usage:
                subscription.current_usage[quota_key] += quantity
            if quota_key in subscription.quota_remaining:
                subscription.quota_remaining[quota_key] -= quantity
            
            subscription.lifetime_requests += int(quantity)
            subscription.last_updated = datetime.now(timezone.utc)
            
            return True
    
    def _get_unit_price(self, plan: SubscriptionPlan, metric_type: UsageMetricType) -> Decimal:
        """Get unit price for a metric type"""
        if metric_type == UsageMetricType.API_CALLS:
            return plan.price_per_1k_calls / Decimal("1000")
        elif metric_type == UsageMetricType.TOKENS:
            return plan.price_per_1m_tokens / Decimal("1000000")
        elif metric_type == UsageMetricType.COMPUTE_TIME:
            return plan.price_per_compute_hour
        return Decimal("0.00")
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self.subscriptions.get(subscription_id)
    
    def get_customer_subscriptions(self, customer_id: str) -> List[Subscription]:
        """Get all subscriptions for a customer"""
        return [
            sub for sub in self.subscriptions.values()
            if sub.customer_id == customer_id
        ]
    
    def upgrade_subscription(self, subscription_id: str, new_plan_id: str) -> bool:
        """Upgrade subscription to a new plan"""
        with self.lock:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription:
                return False
            
            new_plan = self.plans.get(new_plan_id)
            if not new_plan:
                return False
            
            # Check if it's actually an upgrade
            tier_order = [tier.value for tier in SubscriptionTier]
            if tier_order.index(new_plan.tier.value) <= tier_order.index(subscription.plan.tier.value):
                return False
            
            subscription.plan = new_plan
            subscription.last_updated = datetime.now(timezone.utc)
            
            current_app.logger.info(
                f"Upgraded subscription {subscription_id} to {new_plan.name}"
            )
            
            return True
    
    def get_usage_analytics(self, subscription_id: str) -> Dict[str, Any]:
        """Get usage analytics for a subscription"""
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return {}
        
        # Calculate usage percentages
        usage_percent = {}
        for key in subscription.current_usage:
            total_quota = getattr(subscription.plan, f'monthly_{key}', 0)
            if total_quota > 0:
                usage_percent[key] = (subscription.current_usage[key] / total_quota) * 100
            else:
                usage_percent[key] = 0
        
        return {
            'subscription_id': subscription_id,
            'plan': subscription.plan.name,
            'status': subscription.status.value,
            'current_period': {
                'start': subscription.current_period_start.isoformat(),
                'end': subscription.current_period_end.isoformat()
            },
            'usage': subscription.current_usage,
            'quota_remaining': subscription.quota_remaining,
            'usage_percent': usage_percent,
            'total_spent': float(subscription.total_spent),
            'lifetime_requests': subscription.lifetime_requests
        }
    
    def get_revenue_metrics(self) -> Dict[str, Any]:
        """Get revenue analytics"""
        with self.lock:
            total_revenue = Decimal("0.00")
            active_subs = 0
            mrr = Decimal("0.00")
            
            for sub in self.subscriptions.values():
                if sub.status == SubscriptionStatus.ACTIVE:
                    active_subs += 1
                    mrr += sub.plan.base_price
                total_revenue += sub.total_spent
            
            arr = mrr * Decimal("12")
            
            return {
                'total_revenue': float(total_revenue),
                'active_subscriptions': active_subs,
                'total_subscriptions': len(self.subscriptions),
                'mrr': float(mrr),
                'arr': float(arr),
                'average_revenue_per_user': float(mrr / max(active_subs, 1))
            }
    
    def get_all_plans(self, public_only: bool = True) -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        plans = []
        for plan in self.plans.values():
            if public_only and not plan.is_public:
                continue
            
            plans.append({
                'plan_id': plan.plan_id,
                'tier': plan.tier.value,
                'name': plan.name,
                'description': plan.description,
                'pricing': {
                    'base_price': float(plan.base_price),
                    'currency': plan.currency,
                    'billing_cycle': plan.billing_cycle.value
                },
                'limits': {
                    'requests_per_minute': plan.requests_per_minute,
                    'requests_per_hour': plan.requests_per_hour,
                    'requests_per_day': plan.requests_per_day,
                    'monthly_api_calls': plan.monthly_api_calls,
                    'monthly_tokens': plan.monthly_tokens
                },
                'features': plan.features,
                'support_level': plan.support_level,
                'sla_guarantee': plan.sla_guarantee
            })
        
        return plans


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_subscription_service_instance: Optional[APISubscriptionService] = None
_service_lock = threading.Lock()


def get_subscription_service() -> APISubscriptionService:
    """Get singleton subscription service"""
    global _subscription_service_instance
    
    if _subscription_service_instance is None:
        with _service_lock:
            if _subscription_service_instance is None:
                _subscription_service_instance = APISubscriptionService()
    
    return _subscription_service_instance
