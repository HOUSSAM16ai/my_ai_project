# app/services/service_catalog_service.py
# ======================================================================================
# ==          SUPERHUMAN SERVICE CATALOG (v1.0 - BACKSTAGE-STYLE)                 ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام Service Catalog خارق يتفوق على Backstage من Spotify
#   ✨ المميزات الخارقة:
#   - Service discovery and documentation
#   - API catalog with OpenAPI specs
#   - Template scaffolding
#   - Service ownership tracking
#   - Tech stack inventory
#   - Service health dashboard

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from flask import current_app

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class ServiceType(Enum):
    """Service types"""

    MICROSERVICE = "microservice"
    API = "api"
    DATABASE = "database"
    QUEUE = "queue"
    CACHE = "cache"
    FRONTEND = "frontend"
    LIBRARY = "library"


class ServiceLifecycle(Enum):
    """Service lifecycle stages"""

    EXPERIMENTAL = "experimental"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class HealthStatus(Enum):
    """Service health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class ServiceMetadata:
    """Service metadata"""

    service_id: str
    name: str
    description: str
    service_type: ServiceType
    lifecycle: ServiceLifecycle
    owner_team: str
    repository_url: str
    documentation_url: str
    api_spec_url: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class APISpec:
    """API specification"""

    spec_id: str
    service_id: str
    spec_type: str  # openapi, graphql, grpc
    version: str
    spec_content: dict[str, Any]
    endpoints: list[dict[str, Any]]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ServiceTemplate:
    """Service template for scaffolding"""

    template_id: str
    name: str
    description: str
    service_type: ServiceType
    tech_stack: list[str]
    files: dict[str, str]  # filename -> content
    parameters: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ServiceHealth:
    """Service health information"""

    service_id: str
    status: HealthStatus
    uptime_percentage: float
    last_checked: datetime
    metrics: dict[str, float]
    incidents: list[dict[str, Any]] = field(default_factory=list)


# ======================================================================================
# SERVICE CATALOG
# ======================================================================================


class ServiceCatalogService:
    """
    خدمة Service Catalog الخارقة - World-class service catalog

    Features:
    - Service discovery and registry
    - API catalog with specs
    - Template-based scaffolding
    - Service ownership tracking
    - Tech stack inventory
    - Health monitoring dashboard
    """

    def __init__(self):
        self.services: dict[str, ServiceMetadata] = {}
        self.api_specs: dict[str, list[APISpec]] = defaultdict(list)
        self.templates: dict[str, ServiceTemplate] = {}
        self.health_status: dict[str, ServiceHealth] = {}
        self.lock = threading.RLock()  # Use RLock to prevent deadlock with nested calls

        # Initialize default templates
        self._initialize_templates()

        current_app.logger.info("Service Catalog initialized successfully")

    def _initialize_templates(self):
        """Initialize default service templates"""
        # Python Flask Microservice
        self.register_template(
            ServiceTemplate(
                template_id="python-flask-microservice",
                name="Python Flask Microservice",
                description="Production-ready Flask microservice",
                service_type=ServiceType.MICROSERVICE,
                tech_stack=["Python", "Flask", "SQLAlchemy", "PostgreSQL"],
                files={
                    "app.py": "# Flask application\nfrom flask import Flask\napp = Flask(__name__)",
                    "requirements.txt": "Flask\nSQLAlchemy\npsycopg2-binary",
                    "Dockerfile": "FROM python:3.11\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt",
                },
                parameters={"service_name": "string", "port": "integer"},
            )
        )

    # ==================================================================================
    # SERVICE REGISTRY
    # ==================================================================================

    def register_service(self, service: ServiceMetadata) -> bool:
        """Register service in catalog"""
        with self.lock:
            self.services[service.service_id] = service

            # Initialize health status
            self.health_status[service.service_id] = ServiceHealth(
                service_id=service.service_id,
                status=HealthStatus.UNKNOWN,
                uptime_percentage=0.0,
                last_checked=datetime.now(UTC),
                metrics={},
            )

            current_app.logger.info(f"Registered service: {service.name}")
            return True

    def get_service(self, service_id: str) -> ServiceMetadata | None:
        """Get service by ID"""
        return self.services.get(service_id)

    def search_services(
        self,
        query: str | None = None,
        service_type: ServiceType | None = None,
        owner_team: str | None = None,
        tags: list[str] | None = None,
    ) -> list[ServiceMetadata]:
        """Search services"""
        results = list(self.services.values())

        if query:
            query_lower = query.lower()
            results = [
                s
                for s in results
                if query_lower in s.name.lower() or query_lower in s.description.lower()
            ]

        if service_type:
            results = [s for s in results if s.service_type == service_type]

        if owner_team:
            results = [s for s in results if s.owner_team == owner_team]

        if tags:
            results = [s for s in results if any(tag in s.tags for tag in tags)]

        return results

    # ==================================================================================
    # API SPECS
    # ==================================================================================

    def register_api_spec(self, spec: APISpec) -> bool:
        """Register API specification"""
        with self.lock:
            self.api_specs[spec.service_id].append(spec)
            current_app.logger.info(f"Registered API spec for {spec.service_id}: {spec.version}")
            return True

    def get_api_specs(self, service_id: str) -> list[APISpec]:
        """Get API specs for service"""
        return self.api_specs.get(service_id, [])

    # ==================================================================================
    # TEMPLATES & SCAFFOLDING
    # ==================================================================================

    def register_template(self, template: ServiceTemplate) -> bool:
        """Register service template"""
        with self.lock:
            self.templates[template.template_id] = template
            return True

    def get_templates(self, service_type: ServiceType | None = None) -> list[ServiceTemplate]:
        """Get available templates"""
        templates = list(self.templates.values())

        if service_type:
            templates = [t for t in templates if t.service_type == service_type]

        return templates

    def scaffold_service(self, template_id: str, parameters: dict[str, Any]) -> dict[str, str]:
        """Scaffold new service from template"""
        template = self.templates.get(template_id)
        if not template:
            return {}

        # Apply parameters to template files
        scaffolded_files = {}
        for filename, content in template.files.items():
            # Simple parameter replacement
            for param_name, param_value in parameters.items():
                content = content.replace(f"{{{param_name}}}", str(param_value))

            scaffolded_files[filename] = content

        return scaffolded_files

    # ==================================================================================
    # HEALTH MONITORING
    # ==================================================================================

    def update_service_health(
        self, service_id: str, status: HealthStatus, metrics: dict[str, float]
    ):
        """Update service health status"""
        with self.lock:
            if service_id in self.health_status:
                health = self.health_status[service_id]
                health.status = status
                health.metrics = metrics
                health.last_checked = datetime.now(UTC)

    def get_service_health(self, service_id: str) -> ServiceHealth | None:
        """Get service health"""
        return self.health_status.get(service_id)

    # ==================================================================================
    # DEPENDENCY GRAPH
    # ==================================================================================

    def get_dependency_graph(self) -> dict[str, Any]:
        """Get service dependency graph"""
        graph = {"nodes": [], "edges": []}

        for service in self.services.values():
            graph["nodes"].append(
                {
                    "id": service.service_id,
                    "name": service.name,
                    "type": service.service_type.value,
                }
            )

            for dep_id in service.dependencies:
                graph["edges"].append({"from": service.service_id, "to": dep_id})

        return graph

    # ==================================================================================
    # METRICS
    # ==================================================================================

    def get_catalog_metrics(self) -> dict[str, Any]:
        """Get catalog metrics"""
        return {
            "total_services": len(self.services),
            "services_by_type": {
                st.value: len([s for s in self.services.values() if s.service_type == st])
                for st in ServiceType
            },
            "services_by_lifecycle": {
                lc.value: len([s for s in self.services.values() if s.lifecycle == lc])
                for lc in ServiceLifecycle
            },
            "total_api_specs": sum(len(specs) for specs in self.api_specs.values()),
            "templates_available": len(self.templates),
            "health_status_summary": {
                "healthy": len(
                    [h for h in self.health_status.values() if h.status == HealthStatus.HEALTHY]
                ),
                "degraded": len(
                    [h for h in self.health_status.values() if h.status == HealthStatus.DEGRADED]
                ),
                "down": len(
                    [h for h in self.health_status.values() if h.status == HealthStatus.DOWN]
                ),
            },
        }


# ======================================================================================
# SINGLETON
# ======================================================================================

_catalog_instance: ServiceCatalogService | None = None
_catalog_lock = threading.Lock()


def get_service_catalog() -> ServiceCatalogService:
    """Get singleton service catalog instance"""
    global _catalog_instance

    if _catalog_instance is None:
        with _catalog_lock:
            if _catalog_instance is None:
                _catalog_instance = ServiceCatalogService()

    return _catalog_instance
