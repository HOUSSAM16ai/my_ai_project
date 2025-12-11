# tests/ai/test_cost_manager.py
"""
Tests for Cost Manager Implementation
======================================
"""

import pytest
import time
from app.ai.application.cost_manager import (
    CostManager,
    BudgetConfig,
    BudgetPeriod,
    BudgetExceededError,
    ModelPricing,
)


class TestCostManager:
    """Test cost management functionality."""
    
    def test_track_usage_calculates_cost(self):
        """Cost manager should calculate cost from token usage."""
        manager = CostManager()
        
        record = manager.track_usage(
            model="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=500,
        )
        
        assert record.cost > 0
        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        
        metrics = manager.get_metrics()
        assert metrics.total_cost == record.cost
        assert metrics.total_requests == 1
    
    def test_cost_tracking_by_model(self):
        """Cost should be tracked per model."""
        manager = CostManager()
        
        manager.track_usage("gpt-4", 1000, 500)
        manager.track_usage("gpt-3.5-turbo", 1000, 500)
        manager.track_usage("gpt-4", 500, 250)
        
        metrics = manager.get_metrics()
        assert "gpt-4" in metrics.cost_by_model
        assert "gpt-3.5-turbo" in metrics.cost_by_model
        assert metrics.cost_by_model["gpt-4"] > metrics.cost_by_model["gpt-3.5-turbo"]
    
    def test_cost_tracking_by_user(self):
        """Cost should be tracked per user."""
        manager = CostManager()
        
        manager.track_usage("gpt-4", 1000, 500, user_id="user1")
        manager.track_usage("gpt-4", 1000, 500, user_id="user2")
        manager.track_usage("gpt-4", 500, 250, user_id="user1")
        
        metrics = manager.get_metrics()
        assert "user1" in metrics.cost_by_user
        assert "user2" in metrics.cost_by_user
        assert metrics.cost_by_user["user1"] > metrics.cost_by_user["user2"]
    
    def test_budget_enforcement_hard_limit(self):
        """Budget hard limit should block requests."""
        manager = CostManager()
        
        manager.set_budget(
            "test_budget",
            BudgetConfig(limit=0.01, period=BudgetPeriod.DAILY)
        )
        
        manager.track_usage("gpt-3.5-turbo", 1000, 500)
        
        with pytest.raises(BudgetExceededError):
            manager.track_usage("gpt-4", 10000, 5000)
    
    def test_budget_status(self):
        """Budget status should show usage and remaining."""
        manager = CostManager()
        
        manager.set_budget(
            "test_budget",
            BudgetConfig(limit=1.0, period=BudgetPeriod.DAILY)
        )
        
        manager.track_usage("gpt-3.5-turbo", 1000, 500)
        
        status = manager.get_budget_status("test_budget")
        assert status["limit"] == 1.0
        assert status["usage"] > 0
        assert status["remaining"] < 1.0
        assert 0 <= status["percentage"] <= 100
    
    def test_custom_model_pricing(self):
        """Custom model pricing should be used."""
        manager = CostManager()
        
        custom_pricing = ModelPricing(
            model_name="custom-model",
            input_cost_per_1k=0.1,
            output_cost_per_1k=0.2,
        )
        manager.register_model_pricing(custom_pricing)
        
        record = manager.track_usage("custom-model", 1000, 1000)
        
        expected_cost = (1000 / 1000 * 0.1) + (1000 / 1000 * 0.2)
        assert abs(record.cost - expected_cost) < 0.001
    
    def test_cost_breakdown(self):
        """Cost breakdown should provide detailed analysis."""
        manager = CostManager()
        
        manager.track_usage("gpt-4", 1000, 500, user_id="user1", project_id="proj1")
        manager.track_usage("gpt-3.5-turbo", 1000, 500, user_id="user2", project_id="proj1")
        
        breakdown = manager.get_cost_breakdown()
        
        assert "total_cost" in breakdown
        assert "by_model" in breakdown
        assert "by_user" in breakdown
        assert "by_project" in breakdown
        assert len(breakdown["by_model"]) == 2
        assert "proj1" in breakdown["by_project"]
    
    def test_monthly_cost_prediction(self):
        """Monthly cost prediction should extrapolate from recent usage."""
        manager = CostManager()
        
        for _ in range(10):
            manager.track_usage("gpt-3.5-turbo", 1000, 500)
        
        predicted = manager.predict_monthly_cost()
        assert predicted > 0
    
    def test_optimization_recommendations(self):
        """Optimization recommendations should be generated."""
        manager = CostManager()
        
        for _ in range(10):
            manager.track_usage("gpt-4", 5000, 2500)
        
        recommendations = manager.get_optimization_recommendations()
        assert isinstance(recommendations, list)
    
    def test_metrics_reset(self):
        """Reset should clear all metrics."""
        manager = CostManager()
        
        manager.track_usage("gpt-4", 1000, 500)
        
        metrics_before = manager.get_metrics()
        assert metrics_before.total_requests > 0
        
        manager.reset_metrics()
        
        metrics_after = manager.get_metrics()
        assert metrics_after.total_requests == 0
        assert metrics_after.total_cost == 0.0
