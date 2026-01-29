from __future__ import annotations

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

__all__ = [
    "APISpec",
    "AllowAllCatalogPolicy",
    "DefaultServiceCatalogPolicy",
    "HealthStatus",
    "ServiceCatalogPolicy",
    "ServiceCatalogService",
    "ServiceHealth",
    "ServiceLifecycle",
    "ServiceMetadata",
    "ServiceTemplate",
    "ServiceType",
    "get_service_catalog",
]


class ServiceType(Enum):
    """أنواع الخدمات ضمن منظومة الميكروسيرفس."""

    MICROSERVICE = "microservice"
    API = "api"
    DATABASE = "database"
    QUEUE = "queue"
    CACHE = "cache"
    FRONTEND = "frontend"
    LIBRARY = "library"


class ServiceLifecycle(Enum):
    """مراحل دورة حياة الخدمة."""

    EXPERIMENTAL = "experimental"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class HealthStatus(Enum):
    """حالة صحة الخدمة."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ServiceMetadata:
    """بيانات وصفية للخدمة ضمن السجل."""

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
    """مواصفة API خاصة بخدمة محددة."""

    spec_id: str
    service_id: str
    spec_type: str
    version: str
    spec_content: dict[str, object]
    endpoints: list[dict[str, object]]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ServiceTemplate:
    """قالب خدمة للتوليد المبدئي."""

    template_id: str
    name: str
    description: str
    service_type: ServiceType
    tech_stack: list[str]
    files: dict[str, str]
    parameters: dict[str, object]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ServiceHealth:
    """معلومات صحة الخدمة."""

    service_id: str
    status: HealthStatus
    uptime_percentage: float
    last_checked: datetime
    metrics: dict[str, float]
    incidents: list[dict[str, object]] = field(default_factory=list)


class ServiceCatalogPolicy(Protocol):
    """واجهة سياسات دليل الخدمات وفق مبدأ الاعتماد على التجريد."""

    def validate_service(self, service: ServiceMetadata) -> None:
        """التحقق من صلاحية تسجيل خدمة."""

    def validate_api_spec(self, spec: APISpec) -> None:
        """التحقق من صلاحية مواصفة API."""


@dataclass(frozen=True, slots=True)
class DefaultServiceCatalogPolicy:
    """السياسة الافتراضية لتطبيق قواعد API-First وميكروسيرفس."""

    def validate_service(self, service: ServiceMetadata) -> None:
        """
        تحقق صارم من التزام الخدمة بمبدأ API-First.

        Raises:
            ValueError: عند انتهاك قواعد الميكروسيرفس الأساسية.
        """
        if not service.service_id.strip():
            raise ValueError("Service ID must be non-empty.")
        if service.service_type == ServiceType.LIBRARY:
            raise ValueError("Shared libraries are forbidden in microservice architecture.")

        # Combine nested if
        if (
            service.service_type in {ServiceType.MICROSERVICE, ServiceType.API}
            and not service.api_spec_url
        ):
            raise ValueError("API spec URL is required for API-first services.")

        if service.service_id in service.dependencies:
            raise ValueError("Service cannot depend on itself.")
        if len(set(service.dependencies)) != len(service.dependencies):
            raise ValueError("Service dependencies must be unique.")

    def validate_api_spec(self, spec: APISpec) -> None:
        """يتحقق من أن المواصفة مرتبطة بخدمة موجودة معرفياً."""
        if not spec.service_id:
            raise ValueError("API spec must be linked to a service_id.")


@dataclass(frozen=True, slots=True)
class AllowAllCatalogPolicy:
    """سياسة اختبارية تسمح بجميع التسجيلات (للاختبارات فقط)."""

    def validate_service(self, service: ServiceMetadata) -> None:
        """لا تطبق أي تحقق."""

    def validate_api_spec(self, spec: APISpec) -> None:
        """لا تطبق أي تحقق."""


class ServiceCatalogService:
    """
    خدمة دليل الخدمات (Service Catalog) بمنهجية API-First.

    الخصائص:
    - اكتشاف الخدمات وتسجيلها.
    - فهرسة مواصفات الـ API لكل خدمة.
    - قوالب توليد لخدمات الميكروسيرفس.
    - تتبع الملكية والاعتماديات.
    - جرد التقنيات ومراقبة الصحة.
    """

    def __init__(self, policy: ServiceCatalogPolicy | None = None) -> None:
        self.services: dict[str, ServiceMetadata] = {}
        self.api_specs: dict[str, list[APISpec]] = defaultdict(list)
        self.templates: dict[str, ServiceTemplate] = {}
        self.health_status: dict[str, ServiceHealth] = {}
        self.lock = threading.RLock()
        self.policy = self._resolve_policy(policy)
        self._initialize_templates()
        logging.getLogger(__name__).info("Service Catalog initialized successfully")

    def _initialize_templates(self) -> None:
        """تهيئة قوالب الخدمات الافتراضية."""
        self.register_template(
            ServiceTemplate(
                template_id="python-fastapi-microservice",
                name="Python FastAPI Microservice",
                description="High-performance FastAPI microservice",
                service_type=ServiceType.MICROSERVICE,
                tech_stack=["Python", "FastAPI", "SQLModel", "PostgreSQL"],
                files={
                    "app.py": """# FastAPI application
from fastapi import FastAPI
app = FastAPI()""",
                    "requirements.txt": """fastapi
uvicorn
sqlmodel""",
                    "Dockerfile": """FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt""",
                },
                parameters={"service_name": "string", "port": "integer"},
            )
        )

    def register_service(self, service: ServiceMetadata) -> bool:
        """تسجيل خدمة في الدليل وفق مبدأ API-First."""
        self.policy.validate_service(service)
        with self.lock:
            self.services[service.service_id] = service
            self.health_status[service.service_id] = ServiceHealth(
                service_id=service.service_id,
                status=HealthStatus.UNKNOWN,
                uptime_percentage=0.0,
                last_checked=datetime.now(UTC),
                metrics={},
            )
            logging.getLogger(__name__).info(f"Registered service: {service.name}")
            return True

    def get_service(self, service_id: str) -> ServiceMetadata | None:
        """استرجاع خدمة عبر المعرّف."""
        return self.services.get(service_id)

    def register_api_spec(self, spec: APISpec) -> bool:
        """تسجيل مواصفة API وربطها بالخدمة."""
        self.policy.validate_api_spec(spec)
        with self.lock:
            self.api_specs[spec.service_id].append(spec)
            logging.getLogger(__name__).info(
                f"Registered API spec for {spec.service_id}: {spec.version}"
            )
            return True

    def get_api_specs(self, service_id: str) -> list[APISpec]:
        """استرجاع مواصفات API لخدمة معينة."""
        return self.api_specs.get(service_id, [])

    def register_template(self, template: ServiceTemplate) -> bool:
        """تسجيل قالب خدمة جديد."""
        with self.lock:
            self.templates[template.template_id] = template
            return True

    def get_templates(self, service_type: ServiceType | None = None) -> list[ServiceTemplate]:
        """استرجاع القوالب المتاحة حسب النوع."""
        templates = list(self.templates.values())
        if service_type:
            templates = [t for t in templates if t.service_type == service_type]
        return templates

    def update_service_health(
        self, service_id: str, status: HealthStatus, metrics: dict[str, float]
    ) -> None:
        """تحديث حالة صحة خدمة معينة."""
        with self.lock:
            if service_id in self.health_status:
                health = self.health_status[service_id]
                health.status = status
                health.metrics = metrics
                health.last_checked = datetime.now(UTC)

    def _resolve_policy(self, policy: ServiceCatalogPolicy | None) -> ServiceCatalogPolicy:
        """حل سياسة الدليل بشكل صريح مع قيمة افتراضية."""
        return policy or DefaultServiceCatalogPolicy()

    def get_service_health(self, service_id: str) -> ServiceHealth | None:
        """استرجاع حالة صحة خدمة محددة."""
        return self.health_status.get(service_id)

    def get_dependency_graph(self) -> dict[str, object]:
        """بناء رسم اعتماديات الخدمات."""
        graph = {"nodes": [], "edges": []}
        for service in self.services.values():
            graph["nodes"].append(
                {"id": service.service_id, "name": service.name, "type": service.service_type.value}
            )
            for dep_id in service.dependencies:
                graph["edges"].append({"from": service.service_id, "to": dep_id})
        return graph

    def get_catalog_metrics(self) -> dict[str, object]:
        """استرجاع مؤشرات الدليل التشغيلية."""
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


_catalog_instance: ServiceCatalogService | None = None
_catalog_lock = threading.Lock()


def get_service_catalog() -> ServiceCatalogService:
    """استرجاع نسخة الدليل وفق نمط Singleton."""
    global _catalog_instance
    if _catalog_instance is None:
        with _catalog_lock:
            if _catalog_instance is None:
                _catalog_instance = ServiceCatalogService()
    return _catalog_instance
