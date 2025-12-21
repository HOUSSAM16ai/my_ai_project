import pytest
from datetime import datetime, UTC
from app.services.system.service_catalog_service import (
    ServiceCatalogService, ServiceMetadata, ServiceType, ServiceLifecycle,
    APISpec, ServiceTemplate, ServiceHealth, HealthStatus, get_service_catalog
)

@pytest.fixture
def catalog():
    return ServiceCatalogService()

def test_initialization(catalog):
    assert len(catalog.templates) > 0 # Should have default template
    metrics = catalog.get_catalog_metrics()
    assert metrics["templates_available"] >= 1

def test_register_get_service(catalog):
    service = ServiceMetadata(
        service_id="svc-1",
        name="Test Service",
        description="Desc",
        service_type=ServiceType.MICROSERVICE,
        lifecycle=ServiceLifecycle.PRODUCTION,
        owner_team="Team A",
        repository_url="http://git",
        documentation_url="http://doc",
        tech_stack=["Python"]
    )

    assert catalog.register_service(service) is True
    assert catalog.get_service("svc-1") == service

    health = catalog.get_service_health("svc-1")
    assert health is not None
    assert health.status == HealthStatus.UNKNOWN

def test_api_spec(catalog):
    spec = APISpec(
        spec_id="spec-1",
        service_id="svc-1",
        spec_type="openapi",
        version="v1",
        spec_content={},
        endpoints=[]
    )
    assert catalog.register_api_spec(spec) is True
    assert len(catalog.get_api_specs("svc-1")) == 1

def test_templates(catalog):
    template = ServiceTemplate(
        template_id="t1",
        name="T1",
        description="D",
        service_type=ServiceType.API,
        tech_stack=[],
        files={},
        parameters={}
    )
    catalog.register_template(template)

    templates = catalog.get_templates(ServiceType.API)
    assert len(templates) == 1
    assert templates[0].template_id == "t1"

    assert len(catalog.get_templates(ServiceType.DATABASE)) == 0

def test_health_update(catalog):
    service = ServiceMetadata(
        service_id="svc-1",
        name="Test Service",
        description="Desc",
        service_type=ServiceType.MICROSERVICE,
        lifecycle=ServiceLifecycle.PRODUCTION,
        owner_team="Team A",
        repository_url="http://git",
        documentation_url="http://doc"
    )
    catalog.register_service(service)

    catalog.update_service_health("svc-1", HealthStatus.HEALTHY, {"cpu": 10.0})
    health = catalog.get_service_health("svc-1")
    assert health.status == HealthStatus.HEALTHY
    assert health.metrics["cpu"] == 10.0

def test_dependency_graph(catalog):
    s1 = ServiceMetadata(
        service_id="s1", name="S1", description="", service_type=ServiceType.API,
        lifecycle=ServiceLifecycle.PRODUCTION, owner_team="", repository_url="", documentation_url="",
        dependencies=["s2"]
    )
    s2 = ServiceMetadata(
        service_id="s2", name="S2", description="", service_type=ServiceType.DATABASE,
        lifecycle=ServiceLifecycle.PRODUCTION, owner_team="", repository_url="", documentation_url="",
        dependencies=[]
    )

    catalog.register_service(s1)
    catalog.register_service(s2)

    graph = catalog.get_dependency_graph()
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
    assert graph["edges"][0]["from"] == "s1"
    assert graph["edges"][0]["to"] == "s2"

def test_metrics_summary(catalog):
    s1 = ServiceMetadata(
        service_id="s1", name="S1", description="", service_type=ServiceType.API,
        lifecycle=ServiceLifecycle.PRODUCTION, owner_team="", repository_url="", documentation_url=""
    )
    catalog.register_service(s1)
    catalog.update_service_health("s1", HealthStatus.HEALTHY, {})

    metrics = catalog.get_catalog_metrics()
    assert metrics["total_services"] == 1
    assert metrics["health_status_summary"]["healthy"] == 1

def test_singleton():
    c1 = get_service_catalog()
    c2 = get_service_catalog()
    assert c1 is c2
