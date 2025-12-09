"""
Tests to fill coverage gaps in critical services.
"""

import threading
import time
from datetime import datetime, UTC
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# === Master Agent Service Tests ===
from app.services.master_agent_service import (
    OvermindService,
    start_mission,
    run_mission_lifecycle,
)
from app.models import User, Mission

class TestMasterAgentService:
    @pytest.fixture
    def mock_deps(self):
        with patch("app.services.master_agent_service.async_session_factory") as mock_session_factory, \
             patch("app.services.master_agent_service.MissionStateManager") as mock_state_manager, \
             patch("app.services.master_agent_service.OvermindOrchestrator") as mock_orchestrator, \
             patch("app.services.master_agent_service.TaskExecutor") as mock_executor, \
             patch("app.services.master_agent_service.asyncio") as mock_asyncio:

            # Setup Async Context Manager for session
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            # Setup State Manager
            mock_state_instance = mock_state_manager.return_value
            mock_mission = MagicMock(spec=Mission)
            mock_mission.id = 123
            mock_state_instance.create_mission.return_value = mock_mission

            yield {
                "session_factory": mock_session_factory,
                "state_manager": mock_state_instance,
                "orchestrator": mock_orchestrator,
                "asyncio": mock_asyncio,
                "mission": mock_mission
            }

    def test_start_new_mission(self, mock_deps):
        service = OvermindService()
        user = MagicMock(spec=User)
        user.id = 1

        # We need to mock _run_sync because it uses asyncio loops which are hard to test in sync tests
        # Also mock _create_mission_async to avoid "coroutine never awaited" warning
        with patch.object(service, '_run_sync') as mock_run_sync, \
             patch.object(service, '_create_mission_async') as mock_create_async, \
             patch("threading.Thread") as mock_thread:

            mock_run_sync.return_value = mock_deps["mission"]

            mission = service.start_new_mission("objective", user)

            assert mission == mock_deps["mission"]
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()

    def test_run_mission_lifecycle(self, mock_deps):
        service = OvermindService()
        with patch.object(service, '_launch_orchestrator_thread') as mock_launch:
            service.run_mission_lifecycle(123)
            mock_launch.assert_called_once_with(123)

    def test_legacy_exports(self, mock_deps):
        # Just verify they don't crash and call the singleton
        with patch("app.services.master_agent_service._overmind_service_singleton") as mock_singleton:
            user = MagicMock(spec=User)
            start_mission("obj", user)
            mock_singleton.start_new_mission.assert_called_once_with("obj", user)

            run_mission_lifecycle(123)
            mock_singleton.run_mission_lifecycle.assert_called_once_with(123)


# === Micro Frontends Service Tests ===
from app.services.micro_frontends_service import (
    MicroFrontendsService,
    get_micro_frontends_service,
    MicroFrontend,
    ModuleFederation,
    FrontendFramework,
    ModuleType,
)

class TestMicroFrontendsService:
    def test_register_module(self):
        service = MicroFrontendsService()
        module = MicroFrontend(
            module_id="mod1",
            name="dashboard",
            module_type=ModuleType.SHELL,
            framework=FrontendFramework.REACT,
            entry_url="/remoteEntry.js",
            exposed_modules={},
            shared_dependencies=[],
            owner_team="core",
            version="1.0.0"
        )

        assert service.register_module(module)
        assert service.get_module("mod1") == module
        assert len(service.get_modules_by_framework(FrontendFramework.REACT)) == 1

    def test_federation(self):
        service = MicroFrontendsService()
        # Register shell
        shell = MicroFrontend(
            module_id="shell", name="shell", module_type=ModuleType.SHELL,
            framework=FrontendFramework.REACT, entry_url="/shell.js",
            exposed_modules={}, shared_dependencies=["react"], owner_team="core", version="1.0"
        )
        service.register_module(shell)

        # Register remote
        remote = MicroFrontend(
            module_id="remote1", name="remote1", module_type=ModuleType.REMOTE,
            framework=FrontendFramework.REACT, entry_url="/remote1.js",
            exposed_modules={"./Widget": "./src/Widget"}, shared_dependencies=["react"], owner_team="feature", version="1.0"
        )
        service.register_module(remote)

        fed = ModuleFederation(
            federation_id="fed1",
            shell_module_id="shell",
            remote_modules=["remote1"],
            shared_state_keys=[],
            routing_config={}
        )

        assert service.create_federation(fed)

        config = service.get_federation_config("fed1")
        assert config["name"] == "shell"
        assert "remote1" in config["remotes"]
        assert "react" in config["shared"]

    def test_shared_state(self):
        service = MicroFrontendsService()
        service.set_shared_state("theme", "dark", "shell")
        assert service.get_shared_state("theme") == "dark"
        assert service.get_shared_state("missing") is None

    def test_metrics(self):
        service = MicroFrontendsService()
        metrics = service.get_metrics()
        assert "total_modules" in metrics

    def test_singleton(self):
        s1 = get_micro_frontends_service()
        s2 = get_micro_frontends_service()
        assert s1 is s2


# === Observability Integration Service Tests ===
from app.services.observability_integration_service import (
    ObservabilityIntegration,
    get_observability,
    MetricType,
    AlertSeverity,
)

class TestObservabilityIntegrationService:
    @pytest.fixture
    def service(self):
        # Patch threading to prevent background threads in tests
        with patch("threading.Thread"):
            return ObservabilityIntegration()

    def test_record_and_get_metrics(self, service):
        service.record_metric("cpu_usage", 50.0, MetricType.GAUGE, {"host": "web1"})
        metrics = service.get_metrics("cpu_usage")
        assert len(metrics) == 1
        assert metrics[0].value == 50.0
        assert metrics[0].labels["host"] == "web1"

    def test_tracing(self, service):
        span = service.start_span("process_request")
        service.add_span_log(span, "processing started")
        service.end_span(span)

        trace = service.get_trace(span.trace_id)
        assert len(trace) == 1
        assert trace[0].operation_name == "process_request"

    def test_alerting(self, service):
        alert_id = service.trigger_alert("high_load", AlertSeverity.WARNING, "Load > 90%", "system")
        alerts = service.get_active_alerts()
        assert len(alerts) == 1
        assert alerts[0].alert_id == alert_id

        service.resolve_alert(alert_id)
        assert len(service.get_active_alerts()) == 0

    def test_health_monitoring(self, service):
        service.update_health_status("db", True, "Connected")
        service.update_health_status("cache", False, "Timeout")

        health = service.get_overall_health()
        assert health["healthy"] is False
        assert health["components"]["db"]["healthy"] is True
        assert health["components"]["cache"]["healthy"] is False

    def test_system_metrics_collection(self, service):
        # Mock dependencies
        with patch.dict("sys.modules", {
            "app.services.deployment_orchestrator_service": MagicMock(),
            "app.services.kubernetes_orchestration_service": MagicMock(),
            "app.services.model_serving_infrastructure": MagicMock(),
        }):
            service._collect_system_metrics()
            # Should not raise exception
            assert True

    def test_singleton(self):
        with patch("threading.Thread"):
            s1 = get_observability()
            s2 = get_observability()
            assert s1 is s2
