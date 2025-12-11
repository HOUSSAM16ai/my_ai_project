# app/ai/application/cost_manager.py
"""
Advanced Cost Management System
================================
Intelligent cost tracking, budget enforcement, and optimization
for LLM API usage.

Features:
- Real-time cost tracking per model/user/project
- Budget enforcement with soft/hard limits
- Cost prediction and forecasting
- Rate limiting based on cost
- Cost optimization recommendations
- Multi-tier pricing support
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class CostTier(Enum):
    """Cost tiers for different usage levels."""
    
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BudgetPeriod(Enum):
    """Budget period types."""
    
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class ModelPricing:
    """Pricing information for a specific model."""
    
    model_name: str
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    context_window: int = 4096
    tier: CostTier = CostTier.BASIC
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate total cost for token usage."""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost


@dataclass
class CostRecord:
    """Record of a single cost transaction."""
    
    timestamp: float
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    user_id: str | None = None
    project_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetConfig:
    """Budget configuration with limits and alerts."""
    
    limit: float
    period: BudgetPeriod
    soft_limit_percentage: float = 0.8  # Alert at 80%
    hard_limit_percentage: float = 1.0  # Block at 100%
    auto_reset: bool = True
    alert_callback: Any = None


@dataclass
class CostMetrics:
    """Aggregated cost metrics."""
    
    total_cost: float = 0.0
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cost_by_model: dict[str, float] = field(default_factory=dict)
    cost_by_user: dict[str, float] = field(default_factory=dict)
    cost_by_project: dict[str, float] = field(default_factory=dict)
    requests_by_model: dict[str, int] = field(default_factory=dict)
    average_cost_per_request: float = 0.0
    peak_cost_per_hour: float = 0.0
    
    def update(self, record: CostRecord) -> None:
        """Update metrics with new cost record."""
        self.total_cost += record.cost
        self.total_requests += 1
        self.total_input_tokens += record.input_tokens
        self.total_output_tokens += record.output_tokens
        
        self.cost_by_model[record.model] = (
            self.cost_by_model.get(record.model, 0.0) + record.cost
        )
        
        if record.user_id:
            self.cost_by_user[record.user_id] = (
                self.cost_by_user.get(record.user_id, 0.0) + record.cost
            )
        
        if record.project_id:
            self.cost_by_project[record.project_id] = (
                self.cost_by_project.get(record.project_id, 0.0) + record.cost
            )
        
        self.requests_by_model[record.model] = (
            self.requests_by_model.get(record.model, 0) + 1
        )
        
        self.average_cost_per_request = self.total_cost / self.total_requests


class CostManager:
    """
    Advanced cost management system for LLM usage.
    
    Provides:
    - Real-time cost tracking
    - Budget enforcement
    - Cost optimization
    - Usage analytics
    
    Thread-safe implementation.
    """
    
    def __init__(self):
        self._pricing: dict[str, ModelPricing] = {}
        self._records: list[CostRecord] = []
        self._metrics = CostMetrics()
        self._budgets: dict[str, BudgetConfig] = {}
        self._budget_usage: dict[str, float] = {}
        self._budget_reset_times: dict[str, float] = {}
        self._lock = threading.RLock()
        
        self._initialize_default_pricing()
    
    def _initialize_default_pricing(self) -> None:
        """Initialize default pricing for common models."""
        default_models = [
            ModelPricing("gpt-4", 0.03, 0.06, 8192, CostTier.PREMIUM),
            ModelPricing("gpt-4-turbo", 0.01, 0.03, 128000, CostTier.PREMIUM),
            ModelPricing("gpt-3.5-turbo", 0.0005, 0.0015, 16385, CostTier.BASIC),
            ModelPricing("claude-3-opus", 0.015, 0.075, 200000, CostTier.PREMIUM),
            ModelPricing("claude-3-sonnet", 0.003, 0.015, 200000, CostTier.BASIC),
            ModelPricing("claude-3-haiku", 0.00025, 0.00125, 200000, CostTier.FREE),
            ModelPricing("gemini-pro", 0.00025, 0.0005, 32768, CostTier.BASIC),
            ModelPricing("llama-2-70b", 0.0007, 0.0009, 4096, CostTier.BASIC),
        ]
        
        for pricing in default_models:
            self._pricing[pricing.model_name] = pricing
    
    def register_model_pricing(self, pricing: ModelPricing) -> None:
        """Register or update pricing for a model."""
        with self._lock:
            self._pricing[pricing.model_name] = pricing
    
    def set_budget(
        self,
        budget_id: str,
        config: BudgetConfig
    ) -> None:
        """Set budget configuration."""
        with self._lock:
            self._budgets[budget_id] = config
            self._budget_usage[budget_id] = 0.0
            self._budget_reset_times[budget_id] = time.time()
    
    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: str | None = None,
        project_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> CostRecord:
        """
        Track LLM usage and calculate cost.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            user_id: Optional user identifier
            project_id: Optional project identifier
            request_id: Optional request identifier
            metadata: Optional additional metadata
            
        Returns:
            CostRecord with calculated cost
            
        Raises:
            BudgetExceededError: If budget limit is exceeded
        """
        with self._lock:
            pricing = self._pricing.get(model)
            if not pricing:
                pricing = ModelPricing(model, 0.001, 0.002)
                self._pricing[model] = pricing
            
            cost = pricing.calculate_cost(input_tokens, output_tokens)
            
            record = CostRecord(
                timestamp=time.time(),
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                user_id=user_id,
                project_id=project_id,
                request_id=request_id,
                metadata=metadata or {}
            )
            
            self._check_budgets(cost, user_id, project_id)
            
            self._records.append(record)
            self._metrics.update(record)
            
            self._update_budget_usage(cost, user_id, project_id)
            
            return record
    
    def _check_budgets(
        self,
        cost: float,
        user_id: str | None,
        project_id: str | None
    ) -> None:
        """Check if cost would exceed any budget limits."""
        for budget_id, config in self._budgets.items():
            if self._should_check_budget(budget_id, user_id, project_id):
                self._reset_budget_if_needed(budget_id, config)
                
                current_usage = self._budget_usage.get(budget_id, 0.0)
                projected_usage = current_usage + cost
                
                hard_limit = config.limit * config.hard_limit_percentage
                soft_limit = config.limit * config.soft_limit_percentage
                
                if projected_usage > hard_limit:
                    raise BudgetExceededError(
                        f"Budget '{budget_id}' hard limit exceeded: "
                        f"${projected_usage:.4f} > ${hard_limit:.4f}"
                    )
                
                if projected_usage > soft_limit and current_usage <= soft_limit:
                    self._trigger_budget_alert(budget_id, projected_usage, config)
    
    def _should_check_budget(
        self,
        budget_id: str,
        user_id: str | None,
        project_id: str | None
    ) -> bool:
        """Determine if budget should be checked for this request."""
        if budget_id == "global":
            return True
        if budget_id.startswith("user:") and user_id:
            return budget_id == f"user:{user_id}"
        if budget_id.startswith("project:") and project_id:
            return budget_id == f"project:{project_id}"
        return False
    
    def _reset_budget_if_needed(
        self,
        budget_id: str,
        config: BudgetConfig
    ) -> None:
        """Reset budget if period has elapsed."""
        if not config.auto_reset:
            return
        
        last_reset = self._budget_reset_times.get(budget_id, 0.0)
        period_seconds = self._get_period_seconds(config.period)
        
        if time.time() - last_reset >= period_seconds:
            self._budget_usage[budget_id] = 0.0
            self._budget_reset_times[budget_id] = time.time()
    
    def _get_period_seconds(self, period: BudgetPeriod) -> float:
        """Convert budget period to seconds."""
        periods = {
            BudgetPeriod.HOURLY: 3600,
            BudgetPeriod.DAILY: 86400,
            BudgetPeriod.WEEKLY: 604800,
            BudgetPeriod.MONTHLY: 2592000,  # 30 days
            BudgetPeriod.YEARLY: 31536000,  # 365 days
        }
        return periods.get(period, 86400)
    
    def _update_budget_usage(
        self,
        cost: float,
        user_id: str | None,
        project_id: str | None
    ) -> None:
        """Update budget usage counters."""
        for budget_id in self._budgets.keys():
            if self._should_check_budget(budget_id, user_id, project_id):
                self._budget_usage[budget_id] = (
                    self._budget_usage.get(budget_id, 0.0) + cost
                )
    
    def _trigger_budget_alert(
        self,
        budget_id: str,
        usage: float,
        config: BudgetConfig
    ) -> None:
        """Trigger budget alert callback."""
        if config.alert_callback:
            try:
                config.alert_callback(budget_id, usage, config.limit)
            except Exception:
                pass
    
    def get_metrics(self) -> CostMetrics:
        """Get current cost metrics."""
        return self._metrics
    
    def get_budget_status(self, budget_id: str) -> dict[str, Any]:
        """Get budget status and usage."""
        with self._lock:
            config = self._budgets.get(budget_id)
            if not config:
                return {}
            
            usage = self._budget_usage.get(budget_id, 0.0)
            percentage = (usage / config.limit) * 100 if config.limit > 0 else 0
            
            return {
                "budget_id": budget_id,
                "limit": config.limit,
                "usage": usage,
                "remaining": max(0, config.limit - usage),
                "percentage": percentage,
                "period": config.period.value,
                "status": self._get_budget_status_label(percentage, config)
            }
    
    def _get_budget_status_label(
        self,
        percentage: float,
        config: BudgetConfig
    ) -> str:
        """Get human-readable budget status."""
        if percentage >= config.hard_limit_percentage * 100:
            return "exceeded"
        elif percentage >= config.soft_limit_percentage * 100:
            return "warning"
        elif percentage >= 50:
            return "normal"
        else:
            return "healthy"
    
    def get_cost_breakdown(
        self,
        start_time: float | None = None,
        end_time: float | None = None
    ) -> dict[str, Any]:
        """Get detailed cost breakdown for time period."""
        with self._lock:
            filtered_records = self._filter_records(start_time, end_time)
            
            breakdown = {
                "total_cost": sum(r.cost for r in filtered_records),
                "total_requests": len(filtered_records),
                "by_model": {},
                "by_user": {},
                "by_project": {},
                "by_hour": {},
            }
            
            for record in filtered_records:
                breakdown["by_model"][record.model] = (
                    breakdown["by_model"].get(record.model, 0.0) + record.cost
                )
                
                if record.user_id:
                    breakdown["by_user"][record.user_id] = (
                        breakdown["by_user"].get(record.user_id, 0.0) + record.cost
                    )
                
                if record.project_id:
                    breakdown["by_project"][record.project_id] = (
                        breakdown["by_project"].get(record.project_id, 0.0) + record.cost
                    )
                
                hour_key = datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:00")
                breakdown["by_hour"][hour_key] = (
                    breakdown["by_hour"].get(hour_key, 0.0) + record.cost
                )
            
            return breakdown
    
    def _filter_records(
        self,
        start_time: float | None,
        end_time: float | None
    ) -> list[CostRecord]:
        """Filter records by time range."""
        filtered = self._records
        
        if start_time:
            filtered = [r for r in filtered if r.timestamp >= start_time]
        
        if end_time:
            filtered = [r for r in filtered if r.timestamp <= end_time]
        
        return filtered
    
    def predict_monthly_cost(self) -> float:
        """Predict monthly cost based on recent usage."""
        with self._lock:
            now = time.time()
            week_ago = now - (7 * 86400)
            recent_records = self._filter_records(week_ago, now)
            
            if not recent_records:
                return 0.0
            
            weekly_cost = sum(r.cost for r in recent_records)
            return (weekly_cost / 7) * 30
    
    def get_optimization_recommendations(self) -> list[str]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        with self._lock:
            if not self._metrics.cost_by_model:
                return recommendations
            
            sorted_models = sorted(
                self._metrics.cost_by_model.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            top_model, top_cost = sorted_models[0]
            total_cost = self._metrics.total_cost
            
            if top_cost / total_cost > 0.7:
                recommendations.append(
                    f"Model '{top_model}' accounts for {(top_cost/total_cost)*100:.1f}% "
                    f"of costs. Consider using a cheaper alternative for non-critical tasks."
                )
            
            avg_tokens = (
                (self._metrics.total_input_tokens + self._metrics.total_output_tokens)
                / self._metrics.total_requests
                if self._metrics.total_requests > 0 else 0
            )
            
            if avg_tokens > 2000:
                recommendations.append(
                    f"Average token usage is {avg_tokens:.0f} per request. "
                    f"Consider prompt optimization to reduce token consumption."
                )
            
            predicted_monthly = self.predict_monthly_cost()
            if predicted_monthly > 1000:
                recommendations.append(
                    f"Predicted monthly cost: ${predicted_monthly:.2f}. "
                    f"Consider implementing caching or request batching."
                )
        
        return recommendations
    
    def reset_metrics(self) -> None:
        """Reset all metrics and records."""
        with self._lock:
            self._records.clear()
            self._metrics = CostMetrics()


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded."""
    pass


# Global cost manager instance
_global_cost_manager = CostManager()


def get_cost_manager() -> CostManager:
    """Get global cost manager instance."""
    return _global_cost_manager
