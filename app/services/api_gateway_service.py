# app/services/api_gateway_service.py
# ======================================================================================
# ==        SUPERHUMAN API GATEWAY SERVICE (v1.0 - ULTIMATE EDITION)                ==
# ======================================================================================
# NOTE: This file is now a compatibility shim for app.core.gateway

from app.core.gateway.cache import IntelligentCache
from app.core.gateway.models import (
    CacheStrategy,
    GatewayRoute,
    LoadBalancerState,
    ModelProvider,
    PolicyRule,
    ProtocolType,
    RoutingDecision,
    RoutingStrategy,
    UpstreamService,
)
from app.core.gateway.policy import PolicyEngine
from app.core.gateway.protocols.base import ProtocolAdapter
from app.core.gateway.protocols.graphql import GraphQLAdapter
from app.core.gateway.protocols.grpc import GRPCAdapter
from app.core.gateway.protocols.rest import RESTAdapter
from app.core.gateway.providers.anthropic import AnthropicAdapter
from app.core.gateway.providers.base import ModelProviderAdapter
from app.core.gateway.providers.openai import OpenAIAdapter
from app.core.gateway.routing import IntelligentRouter
from app.core.gateway.service import (
    APIGatewayService,
    api_gateway_service,
    gateway_process,
    get_gateway_service,
)

__all__ = [
    "APIGatewayService",
    "AnthropicAdapter",
    "CacheStrategy",
    "GRPCAdapter",
    "GatewayRoute",
    "GraphQLAdapter",
    "IntelligentCache",
    "IntelligentRouter",
    "LoadBalancerState",
    "ModelProvider",
    "ModelProviderAdapter",
    "OpenAIAdapter",
    "PolicyEngine",
    "PolicyRule",
    "ProtocolAdapter",
    "ProtocolType",
    "RESTAdapter",
    "RoutingDecision",
    "RoutingStrategy",
    "UpstreamService",
    "api_gateway_service",
    "gateway_process",
    "get_gateway_service",
]
