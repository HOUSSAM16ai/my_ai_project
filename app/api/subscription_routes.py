# app/api/subscription_routes.py
# ======================================================================================
# ==    SUPERHUMAN SUBSCRIPTION API ROUTES (v1.0)                                  ==
# ======================================================================================

from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from app.middleware.decorators import monitor_performance, rate_limit, require_jwt_auth
from app.services.api_subscription_service import (
    BillingCycle,
    SubscriptionTier,
    UsageMetricType,
    get_subscription_service,
)

# Create blueprint
api_bp = Blueprint("subscription_api", __name__, url_prefix="/api")


# ======================================================================================
# SUBSCRIPTION PLANS
# ======================================================================================


@api_bp.route("/subscription/plans", methods=["GET"])
@rate_limit
@monitor_performance
def list_subscription_plans():
    """
    List all available subscription plans

    Query Parameters:
    - public_only: Show only public plans (default: true)
    """
    try:
        service = get_subscription_service()
        public_only = request.args.get("public_only", "true").lower() == "true"

        plans = service.get_all_plans(public_only=public_only)

        return jsonify({"status": "success", "data": {"plans": plans, "total": len(plans)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error listing subscription plans: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve subscription plans"}), 500


# ======================================================================================
# SUBSCRIPTION MANAGEMENT
# ======================================================================================


@api_bp.route("/subscription", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def create_subscription():
    """
    Create a new subscription

    Request Body:
    {
        "customer_id": "cust_123",
        "plan_id": "free",
        "trial_days": 14,
        "metadata": {}
    }
    """
    try:
        data = request.get_json()

        if not data or "customer_id" not in data or "plan_id" not in data:
            return (
                jsonify({"status": "error", "message": "customer_id and plan_id are required"}),
                400,
            )

        service = get_subscription_service()

        subscription = service.create_subscription(
            customer_id=data["customer_id"],
            plan_id=data["plan_id"],
            trial_days=data.get("trial_days", 0),
            metadata=data.get("metadata"),
        )

        if not subscription:
            return (
                jsonify(
                    {"status": "error", "message": "Failed to create subscription. Plan not found."}
                ),
                404,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "subscription_id": subscription.subscription_id,
                        "customer_id": subscription.customer_id,
                        "plan": subscription.plan.name,
                        "status": subscription.status.value,
                        "created_at": subscription.created_at.isoformat(),
                    },
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to create subscription"}), 500


@api_bp.route("/subscription/<subscription_id>", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_subscription(subscription_id: str):
    """Get subscription details"""
    try:
        service = get_subscription_service()
        subscription = service.get_subscription(subscription_id)

        if not subscription:
            return jsonify({"status": "error", "message": "Subscription not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "subscription_id": subscription.subscription_id,
                        "customer_id": subscription.customer_id,
                        "plan": {
                            "name": subscription.plan.name,
                            "tier": subscription.plan.tier.value,
                            "base_price": float(subscription.plan.base_price),
                        },
                        "status": subscription.status.value,
                        "current_period": {
                            "start": subscription.current_period_start.isoformat(),
                            "end": subscription.current_period_end.isoformat(),
                        },
                        "usage": subscription.current_usage,
                        "quota_remaining": subscription.quota_remaining,
                        "total_spent": float(subscription.total_spent),
                        "lifetime_requests": subscription.lifetime_requests,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error retrieving subscription: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve subscription"}), 500


@api_bp.route("/subscription/<subscription_id>/upgrade", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def upgrade_subscription(subscription_id: str):
    """
    Upgrade subscription to a new plan

    Request Body:
    {
        "new_plan_id": "pro"
    }
    """
    try:
        data = request.get_json()

        if not data or "new_plan_id" not in data:
            return jsonify({"status": "error", "message": "new_plan_id is required"}), 400

        service = get_subscription_service()
        success = service.upgrade_subscription(subscription_id, data["new_plan_id"])

        if not success:
            return jsonify({"status": "error", "message": "Failed to upgrade subscription"}), 400

        return jsonify({"status": "success", "message": "Subscription upgraded successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error upgrading subscription: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to upgrade subscription"}), 500


# ======================================================================================
# USAGE TRACKING
# ======================================================================================


@api_bp.route("/subscription/<subscription_id>/usage", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def record_usage(subscription_id: str):
    """
    Record API usage

    Request Body:
    {
        "metric_type": "api_calls",
        "quantity": 1,
        "endpoint": "/api/users",
        "metadata": {}
    }
    """
    try:
        data = request.get_json()

        if not data or "metric_type" not in data or "quantity" not in data:
            return (
                jsonify({"status": "error", "message": "metric_type and quantity are required"}),
                400,
            )

        service = get_subscription_service()

        # Convert string to enum
        try:
            metric_type = UsageMetricType[data["metric_type"].upper()]
        except KeyError:
            return (
                jsonify(
                    {"status": "error", "message": f"Invalid metric_type: {data['metric_type']}"}
                ),
                400,
            )

        success = service.record_usage(
            subscription_id=subscription_id,
            metric_type=metric_type,
            quantity=float(data["quantity"]),
            endpoint=data.get("endpoint"),
            metadata=data.get("metadata"),
        )

        if not success:
            return (
                jsonify(
                    {"status": "error", "message": "Failed to record usage. Quota may be exceeded."}
                ),
                429,
            )

        return jsonify({"status": "success", "message": "Usage recorded successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error recording usage: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to record usage"}), 500


@api_bp.route("/subscription/<subscription_id>/analytics", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_subscription_analytics(subscription_id: str):
    """Get usage analytics for a subscription"""
    try:
        service = get_subscription_service()
        analytics = service.get_usage_analytics(subscription_id)

        if not analytics:
            return jsonify({"status": "error", "message": "Subscription not found"}), 404

        return jsonify({"status": "success", "data": analytics}), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving analytics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve analytics"}), 500


# ======================================================================================
# REVENUE METRICS
# ======================================================================================


@api_bp.route("/subscription/metrics/revenue", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_revenue_metrics():
    """Get revenue analytics"""
    try:
        service = get_subscription_service()
        metrics = service.get_revenue_metrics()

        return jsonify({"status": "success", "data": metrics}), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving revenue metrics: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve revenue metrics"}), 500


@api_bp.route("/subscription/customer/<customer_id>", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_customer_subscriptions(customer_id: str):
    """Get all subscriptions for a customer"""
    try:
        service = get_subscription_service()
        subscriptions = service.get_customer_subscriptions(customer_id)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "customer_id": customer_id,
                        "subscriptions": [
                            {
                                "subscription_id": sub.subscription_id,
                                "plan": sub.plan.name,
                                "status": sub.status.value,
                                "created_at": sub.created_at.isoformat(),
                            }
                            for sub in subscriptions
                        ],
                        "total": len(subscriptions),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error retrieving customer subscriptions: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve customer subscriptions"}),
            500,
        )
