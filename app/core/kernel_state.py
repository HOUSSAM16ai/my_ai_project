"""
إدارة حالة النواة (Kernel State Management).

يبني حالة التطبيق كبيانات واضحة ويطبقها على كائن FastAPI
وفق مبدأ: Functional Core, Imperative Shell.
"""

from dataclasses import dataclass

from fastapi import FastAPI

from app.core.event_bus_impl import get_event_bus
from app.core.protocols import EventBusProtocol
from app.gateway import APIGateway, ServiceRegistry
from app.gateway.config import DEFAULT_GATEWAY_CONFIG, GatewayConfig
from app.services.overmind.factory import create_langgraph_service
from app.services.overmind.langgraph.service import LangGraphAgentService
from app.services.overmind.plan_registry import AgentPlanRegistry
from app.services.overmind.plan_service import AgentPlanService

__all__ = [
    "AppStateServices",
    "GatewayComponents",
    "apply_app_state",
    "build_app_state",
    "build_gateway_components",
]


@dataclass(frozen=True, slots=True)
class GatewayComponents:
    """حاوية مكونات البوابة لضمان تجميع منظم وقابل للاختبار."""

    registry: ServiceRegistry
    gateway: APIGateway


@dataclass(frozen=True, slots=True)
class AppStateServices:
    """حاوية حالة التطبيق المنسقة كبيانات صريحة."""

    agent_plan_registry: AgentPlanRegistry
    agent_plan_service: AgentPlanService
    langgraph_service: LangGraphAgentService
    event_bus: EventBusProtocol
    service_registry: ServiceRegistry
    api_gateway: APIGateway


def build_gateway_components(
    config: GatewayConfig = DEFAULT_GATEWAY_CONFIG,
) -> GatewayComponents:
    """يبني مكونات بوابة API في حاوية واحدة لضمان الاتساق."""
    registry = ServiceRegistry(services=config.services)
    gateway = APIGateway(config=config, registry=registry)
    return GatewayComponents(registry=registry, gateway=gateway)


def build_app_state() -> AppStateServices:
    """
    يبني حالة التطبيق كبيانات صريحة بدون تأثيرات جانبية.

    Returns:
        AppStateServices: الحاوية الكاملة لحالة النظام.
    """
    gateway_components = build_gateway_components()
    return AppStateServices(
        agent_plan_registry=AgentPlanRegistry(),
        agent_plan_service=AgentPlanService(),
        langgraph_service=create_langgraph_service(),
        event_bus=get_event_bus(),
        service_registry=gateway_components.registry,
        api_gateway=gateway_components.gateway,
    )


def apply_app_state(app: FastAPI, state: AppStateServices) -> None:
    """
    يطبق حالة التطبيق على كائن FastAPI بشكل صريح.

    Args:
        app: كائن FastAPI الأساسي.
        state: حاوية حالة التطبيق.
    """
    app.state.agent_plan_registry = state.agent_plan_registry
    app.state.agent_plan_service = state.agent_plan_service
    app.state.langgraph_service = state.langgraph_service
    app.state.event_bus = state.event_bus
    app.state.service_registry = state.service_registry
    app.state.api_gateway = state.api_gateway
