
import pytest
import time
from unittest.mock import MagicMock
from app.ai.application.cost_manager import (
    CostManager,
    ModelPricing,
    CostTier,
    BudgetConfig,
    BudgetPeriod,
    BudgetExceededError,
    get_cost_manager,
    CostRecord,
    CostMetrics
)

class TestCostManager:

    @pytest.fixture
    def manager(self):
        return CostManager()

    def test_default_pricing_initialization(self, manager):
        assert "gpt-4" in manager._pricing
        assert manager._pricing["gpt-4"].input_cost_per_1k == 0.03
        assert manager._pricing["gpt-4"].tier == CostTier.PREMIUM

    def test_register_model_pricing(self, manager):
        new_model = ModelPricing(
            model_name="new-model",
            input_cost_per_1k=0.01,
            output_cost_per_1k=0.02,
            tier=CostTier.BASIC
        )
        manager.register_model_pricing(new_model)
        assert manager._pricing["new-model"] == new_model

    def test_calculate_cost(self):
        pricing = ModelPricing(
            model_name="test",
            input_cost_per_1k=1.0,
            output_cost_per_1k=2.0
        )
        # 1000 input tokens = $1, 1000 output tokens = $2
        cost = pricing.calculate_cost(1000, 1000)
        assert cost == 3.0

    def test_track_usage_basic(self, manager):
        record = manager.track_usage(
            model="gpt-4",
            input_tokens=1000,
            output_tokens=1000
        )
        # 0.03 + 0.06 = 0.09
        assert pytest.approx(record.cost) == 0.09
        assert len(manager._records) == 1
        assert manager._metrics.total_requests == 1

    def test_track_usage_unknown_model(self, manager):
        # Should create default pricing (0.001 / 0.002)
        record = manager.track_usage("unknown", 1000, 1000)
        # 0.001 + 0.002 = 0.003
        assert pytest.approx(record.cost) == 0.003
        assert "unknown" in manager._pricing

    def test_metrics_update(self, manager):
        manager.track_usage("gpt-4", 1000, 0, user_id="u1", project_id="p1")
        manager.track_usage("gpt-4", 0, 1000, user_id="u1", project_id="p1")

        metrics = manager.get_metrics()
        assert metrics.total_requests == 2
        assert metrics.total_input_tokens == 1000
        assert metrics.total_output_tokens == 1000
        assert "gpt-4" in metrics.cost_by_model
        assert "u1" in metrics.cost_by_user
        assert "p1" in metrics.cost_by_project

    def test_budget_hard_limit(self, manager):
        config = BudgetConfig(limit=1.0, period=BudgetPeriod.DAILY, hard_limit_percentage=1.0)
        manager.set_budget("global", config)

        # Cost is 0.09
        manager.track_usage("gpt-4", 1000, 1000)

        # Now try to exceed $1.0.  (1.0 - 0.09 = 0.91 remaining)
        # Need cost > 0.91. Let's do huge usage.
        # Cost = 0.03 * X + 0.06 * X = 0.09 * X (per 1k)
        # Need X=12000 => 12 * 0.09 = 1.08 > 1.0

        with pytest.raises(BudgetExceededError):
            manager.track_usage("gpt-4", 12000, 12000)

    def test_budget_soft_limit_alert(self, manager):
        mock_callback = MagicMock()
        config = BudgetConfig(
            limit=1.0,
            period=BudgetPeriod.DAILY,
            soft_limit_percentage=0.5,
            alert_callback=mock_callback
        )
        manager.set_budget("global", config)

        # Usage = 0.6 (> 0.5 limit)
        # 1000 tokens ~ 0.09 cost.
        # 6000 tokens ~ 0.54 cost.
        # 7000 tokens ~ 0.63 cost.
        manager.track_usage("gpt-4", 7000, 7000)

        mock_callback.assert_called_once()

    def test_scoped_budgets(self, manager):
        user_config = BudgetConfig(limit=0.1, period=BudgetPeriod.DAILY)
        project_config = BudgetConfig(limit=10.0, period=BudgetPeriod.DAILY)

        manager.set_budget("user:u1", user_config)
        manager.set_budget("project:p1", project_config)

        # Should affect user:u1 budget
        manager.track_usage("gpt-4", 1000, 1000, user_id="u1")
        assert manager.get_budget_status("user:u1")["usage"] > 0

        # Should NOT affect user:u2
        manager.track_usage("gpt-4", 1000, 1000, user_id="u2")
        # u1 usage should not increase
        u1_usage = manager.get_budget_status("user:u1")["usage"]
        assert pytest.approx(u1_usage) == 0.09 # Only from first call

    def test_budget_reset(self, manager):
        config = BudgetConfig(limit=1.0, period=BudgetPeriod.HOURLY)
        manager.set_budget("global", config)

        manager.track_usage("gpt-4", 1000, 1000)
        usage_before = manager.get_budget_status("global")["usage"]
        assert usage_before > 0

        # Manipulate time to simulate period elapsed
        manager._budget_reset_times["global"] -= 4000 # > 1 hour ago

        # Next usage should trigger reset
        manager.track_usage("gpt-4", 100, 100)

        # Usage should be only the new usage
        usage_after = manager.get_budget_status("global")["usage"]
        new_cost = 0.009 # approx
        assert pytest.approx(usage_after, abs=0.01) == new_cost

    def test_get_period_seconds(self, manager):
        assert manager._get_period_seconds(BudgetPeriod.HOURLY) == 3600
        assert manager._get_period_seconds(BudgetPeriod.YEARLY) == 31536000

    def test_get_budget_status_label(self, manager):
        config = BudgetConfig(limit=100, period=BudgetPeriod.DAILY, soft_limit_percentage=0.8)

        assert manager._get_budget_status_label(90, config) == "warning"
        assert manager._get_budget_status_label(40, config) == "healthy"
        assert manager._get_budget_status_label(60, config) == "normal"
        assert manager._get_budget_status_label(100, config) == "exceeded"

    def test_get_cost_breakdown(self, manager):
        t1 = time.time()
        manager.track_usage("gpt-4", 1000, 1000, user_id="u1")
        t2 = time.time()

        breakdown = manager.get_cost_breakdown(start_time=t1-1, end_time=t2+1)
        assert breakdown["total_requests"] == 1
        assert "gpt-4" in breakdown["by_model"]

        # Test filtering
        empty_breakdown = manager.get_cost_breakdown(start_time=t2+100)
        assert empty_breakdown["total_requests"] == 0

    def test_predict_monthly_cost(self, manager):
        # 1 request in last week
        manager.track_usage("gpt-4", 1000, 1000)
        # Cost ~ 0.09
        # Weekly cost = 0.09
        # Monthly = (0.09 / 7) * 30 ~ 0.38
        prediction = manager.predict_monthly_cost()
        assert prediction > 0

    def test_optimization_recommendations(self, manager):
        # 1. High cost model dominance
        # Add expensive usage
        for _ in range(10):
            manager.track_usage("gpt-4", 10000, 10000)

        recs = manager.get_optimization_recommendations()
        assert any("accounts for" in r for r in recs)
        assert any("gpt-4" in r for r in recs)

        # 2. High token usage
        recs2 = manager.get_optimization_recommendations()
        assert any("Average token usage" in r for r in recs2)

    def test_reset_metrics(self, manager):
        manager.track_usage("gpt-4", 100, 100)
        manager.reset_metrics()
        assert len(manager._records) == 0
        assert manager._metrics.total_requests == 0

    def test_get_global_instance(self):
        inst = get_cost_manager()
        assert isinstance(inst, CostManager)
