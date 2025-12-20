"""
Service

هذا الملف جزء من مشروع CogniForge.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from .cache import IntelligentCache
from .models import GatewayRoute, PolicyRule, ProtocolType, UpstreamService
from .policy import PolicyEngine
from .protocols.base import ProtocolAdapter
from .protocols.graphql import GraphQLAdapter
from .protocols.grpc import GRPCAdapter
from .protocols.rest import RESTAdapter
from .routing import IntelligentRouter

logger = logging.getLogger(__name__)


class APIGatewayService:
    """
    خدمة بوابة API الخارقة - Superhuman API Gateway Service

    Features:
    - Unified API reception layer
    - Protocol adapters (REST/GraphQL/gRPC)
    - Intelligent routing engine
    - Dynamic caching
    - Policy enforcement
    - Load balancing
    - Circuit breaker pattern
    - A/B testing support
    - Observability integration
    """

    def __init__(self):
        self.protocol_adapters: dict[str, ProtocolAdapter] = {
            ProtocolType.REST.value: RESTAdapter(),
            ProtocolType.GRAPHQL.value: GraphQLAdapter(),
            ProtocolType.GRPC.value: GRPCAdapter(),
        }
        self.intelligent_router = IntelligentRouter()
        self.cache = IntelligentCache(max_size_mb=100)
        self.policy_engine = PolicyEngine()
        self.routes: dict[str, GatewayRoute] = {}
        self.upstream_services: dict[str, UpstreamService] = {}

        # Initialize default policies
        self._initialize_default_policies()

        logger.info("API Gateway Service initialized successfully")

    def _initialize_default_policies(self):
        """Initialize default security policies"""
        # Example: Block requests without authentication
        self.policy_engine.add_policy(
            PolicyRule(
                rule_id="require_auth",
                name="Require Authentication",
                condition="auth_required and not authenticated",
                action="deny",
                priority=100,
                enabled=True,
            )
        )

    def register_route(self, route: GatewayRoute):
        """Register a gateway route"""
        self.routes[route.route_id] = route
        logger.info(f"Registered route: {route.route_id} -> {route.path_pattern}")

    def register_upstream_service(self, service: UpstreamService):
        """Register an upstream service"""
        self.upstream_services[service.service_id] = service
        logger.info(f"Registered upstream service: {service.service_id}")

    async def process_request(
        self,
        request: Request,
        protocol: ProtocolType = ProtocolType.REST,
        route_id: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        معالجة الطلب عبر البوابة - Process request through gateway

        Returns:
            (response_data, status_code) tuple
        """
        start_time = time.time()

        try:
            # 1. Protocol Adaptation
            adapter = self.protocol_adapters.get(protocol.value)
            if not adapter:
                return {"error": f"Unsupported protocol: {protocol.value}"}, 400

            # Validate request
            is_valid, error_msg = await adapter.validate_request(request)
            if not is_valid:
                return {"error": error_msg}, 400

            # Transform request
            request_data = await adapter.transform_request(request)

            # 2. Policy Enforcement
            # In FastAPI we might use dependency injection for user, here we try to extract it from request state if available
            user_id = getattr(request.state, "user_id", None)

            request_context = {
                "user_id": user_id,
                "endpoint": request.url.path,
                "method": request.method,
                "authenticated": user_id is not None,
            }

            allowed, deny_reason = self.policy_engine.evaluate(request_context)
            if not allowed:
                return {"error": deny_reason, "status": "forbidden"}, 403

            # 3. Check Cache
            cached_response = self.cache.get(request_data)
            if cached_response:
                cached_response["cache_hit"] = True
                return cached_response, 200

            # 4. Route Request (placeholder for actual upstream call)
            # In production, this would call the actual upstream service
            response_data = {
                "status": "success",
                "message": "Gateway processed request",
                "gateway_version": "1.0",
                "protocol": protocol.value,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "cache_hit": False,
            }

            # 5. Cache Response (for cacheable requests)
            if request.method == "GET":
                self.cache.put(request_data, response_data, ttl_seconds=300)

            return response_data, 200

        except Exception as e:
            logger.error(f"Gateway processing error: {e}", exc_info=True)
            return {
                "error": "Internal gateway error",
                "status": "error",
                "message": str(e),
            }, 500

    def get_gateway_stats(self) -> dict[str, Any]:
        """Get comprehensive gateway statistics"""
        return {
            "routes_registered": len(self.routes),
            "upstream_services": len(self.upstream_services),
            "cache_stats": self.cache.get_stats(),
            "policy_violations": len(self.policy_engine.get_violations(limit=100)),
            "protocols_supported": list(self.protocol_adapters.keys()),
        }


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

api_gateway_service = APIGatewayService()


# ======================================================================================
# DECORATOR FOR GATEWAY PROCESSING
# ======================================================================================


def gateway_process(
    protocol: ProtocolType = ProtocolType.REST, _cacheable: bool = False
):
    """
    Decorator to process requests through API Gateway (FastAPI Dependency Injection Friendly)

    Usage:
        @router.get("/my-endpoint")
        @gateway_process(protocol=ProtocolType.REST, _cacheable=True)
        async def my_endpoint(request: Request):
            ...
    """

    # Note: In FastAPI, decorators that wrap route handlers need to match the signature or use dependencies.
    # This is a simplified adaptation.
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            gateway = api_gateway_service

            # Process through gateway
            response_data, status_code = await gateway.process_request(
                request, protocol=protocol
            )

            if status_code != 200:
                return JSONResponse(content=response_data, status_code=status_code)

            # Call original function
            try:
                result = await f(request, *args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Endpoint error: {e}", exc_info=True)
                return JSONResponse(
                    content={"error": "Internal error", "message": str(e)},
                    status_code=500,
                )

        return decorated_function

    return decorator


def get_gateway_service() -> APIGatewayService:
    """Get the singleton instance of APIGatewayService"""
    return api_gateway_service
