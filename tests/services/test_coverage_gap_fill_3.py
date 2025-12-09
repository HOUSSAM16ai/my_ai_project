"""
Tests for Coverage Gap Fill 3
=============================
"""

import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# === Refactoring Tool Tests ===
from app.services.refactoring_tool import RefactorTool


class TestRefactoringTool:
    @pytest.fixture
    def mock_llm(self):
        mock = MagicMock()
        mock.chat.completions.create.return_value.choices.message.content = "refactored code"
        return mock

    @pytest.fixture
    def tool(self, mock_llm):
        return RefactorTool(mock_llm)

    def test_apply_code_refactoring_success(self, tool):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("original code")
            f_path = f.name

        try:
            # Mock build diff to return something
            with patch("app.services.refactoring_tool.difflib.unified_diff", return_value=["diff"]):
                res = tool.apply_code_refactoring(
                    f_path, "improve", dry_run=False, create_backup=True
                )

            assert res.changed is True
            assert res.wrote is True
            assert res.backup_path is not None
            assert Path(res.backup_path).exists()
            assert Path(f_path).read_text() == "refactored code"
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)
            if res.backup_path and os.path.exists(res.backup_path):
                os.remove(res.backup_path)

    def test_apply_code_refactoring_file_not_found(self, tool):
        res = tool.apply_code_refactoring("missing.py", "req")
        assert res.changed is False
        assert "not found" in res.message

    def test_apply_code_refactoring_llm_error(self, tool):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("code")
            f_path = f.name

        tool.llm_client.chat.completions.create.side_effect = Exception("API Error")

        try:
            res = tool.apply_code_refactoring(f_path, "req")
            assert res.changed is False
            assert "LLM call failed" in res.message
        finally:
            os.remove(f_path)

    def test_dry_run(self, tool):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("code")
            f_path = f.name

        try:
            with patch("app.services.refactoring_tool.difflib.unified_diff", return_value=["diff"]):
                res = tool.apply_code_refactoring(f_path, "req", dry_run=True)

            assert res.changed is True
            assert res.wrote is False
            assert Path(f_path).read_text() == "code"  # Not changed
        finally:
            os.remove(f_path)


# === Repo Inspector Service Tests ===
from app.services.repo_inspector_service import (
    count_files,
    files_by_extension,
    get_project_summary,
    total_lines_of_code,
)


class TestRepoInspectorService:
    @pytest.fixture
    def test_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # IMPORTANT: Patch IGNORED_DIRS to avoid ignoring /tmp
            # We copy the original set and remove 'tmp' if present
            from app.services import repo_inspector_service

            original_ignored = repo_inspector_service.IGNORED_DIRS.copy()
            if "tmp" in repo_inspector_service.IGNORED_DIRS:
                repo_inspector_service.IGNORED_DIRS.remove("tmp")

            p = Path(tmpdir)
            (p / "main.py").write_text("print('hello')\n" * 10)
            (p / "utils.js").write_text("console.log('hi');")
            (p / "dist").mkdir()
            (p / "dist" / "build.js").write_text("ignore me")
            (p / ".hidden").write_text("hidden")

            yield tmpdir

            # Restore
            repo_inspector_service.IGNORED_DIRS = original_ignored

    def test_count_files(self, test_dir):
        # Should count main.py, utils.js. Ignore dist/build.js (in IGNORED_DIRS list in service)
        # Wait, 'dist' is in IGNORED_DIRS.
        # .hidden ignored by default
        assert count_files(test_dir) == 2
        assert count_files(test_dir, include_hidden=True) == 3

    def test_files_by_extension(self, test_dir):
        stats = files_by_extension(test_dir)
        assert stats[".py"] == 1
        assert stats[".js"] == 1

    def test_total_lines_of_code(self, test_dir):
        # main.py = 10 lines. utils.js = 1 line.
        assert total_lines_of_code(test_dir, exts=[".py"]) == 10
        assert total_lines_of_code(test_dir, exts=[".js"]) == 1
        assert total_lines_of_code(test_dir) == 11

    def test_get_project_summary(self, test_dir):
        # Mock "." to be test_dir
        with patch("app.services.repo_inspector_service.count_files") as mock_count:
            mock_count.return_value = 10
            summary = get_project_summary()
            assert summary["total_files"] == 10


# === Service Catalog Service Tests ===
from app.services.service_catalog_service import (
    APISpec,
    HealthStatus,
    ServiceCatalogService,
    ServiceLifecycle,
    ServiceMetadata,
    ServiceTemplate,
    ServiceType,
    get_service_catalog,
)


class TestServiceCatalogService:
    def test_register_and_get_service(self):
        catalog = ServiceCatalogService()
        svc = ServiceMetadata(
            service_id="s1",
            name="S1",
            description="desc",
            service_type=ServiceType.API,
            lifecycle=ServiceLifecycle.PRODUCTION,
            owner_team="team",
            repository_url="url",
            documentation_url="doc",
        )
        assert catalog.register_service(svc)
        assert catalog.get_service("s1") == svc

    def test_search_services(self):
        catalog = ServiceCatalogService()
        s1 = ServiceMetadata(
            service_id="s1",
            name="Alpha Service",
            description="desc",
            service_type=ServiceType.API,
            lifecycle=ServiceLifecycle.PRODUCTION,
            owner_team="teamA",
            repository_url="url",
            documentation_url="doc",
        )
        s2 = ServiceMetadata(
            service_id="s2",
            name="Beta Service",
            description="desc",
            service_type=ServiceType.DATABASE,
            lifecycle=ServiceLifecycle.PRODUCTION,
            owner_team="teamB",
            repository_url="url",
            documentation_url="doc",
        )
        catalog.register_service(s1)
        catalog.register_service(s2)

        assert len(catalog.search_services(query="Alpha")) == 1
        assert len(catalog.search_services(service_type=ServiceType.DATABASE)) == 1
        assert len(catalog.search_services(owner_team="teamA")) == 1

    def test_api_specs(self):
        catalog = ServiceCatalogService()
        spec = APISpec("spec1", "s1", "openapi", "v1", {}, [])
        assert catalog.register_api_spec(spec)
        assert len(catalog.get_api_specs("s1")) == 1

    def test_templates_scaffolding(self):
        catalog = ServiceCatalogService()
        # Default template exists
        assert len(catalog.get_templates()) > 0

        tpl = ServiceTemplate(
            "t1", "T1", "desc", ServiceType.API, [], {"f1": "content {var}"}, {"var": "str"}
        )
        catalog.register_template(tpl)

        scaffold = catalog.scaffold_service("t1", {"var": "val"})
        assert scaffold["f1"] == "content val"

    def test_health(self):
        catalog = ServiceCatalogService()
        svc = ServiceMetadata(
            service_id="s1",
            name="S1",
            description="desc",
            service_type=ServiceType.API,
            lifecycle=ServiceLifecycle.PRODUCTION,
            owner_team="team",
            repository_url="url",
            documentation_url="doc",
        )
        catalog.register_service(svc)

        catalog.update_service_health("s1", HealthStatus.HEALTHY, {"uptime": 1.0})
        health = catalog.get_service_health("s1")
        assert health.status == HealthStatus.HEALTHY

    def test_dependency_graph(self):
        catalog = ServiceCatalogService()
        s1 = ServiceMetadata(
            service_id="s1",
            name="S1",
            description="desc",
            service_type=ServiceType.API,
            lifecycle=ServiceLifecycle.PRODUCTION,
            owner_team="team",
            repository_url="url",
            documentation_url="doc",
            dependencies=["s2"],
        )
        catalog.register_service(s1)
        graph = catalog.get_dependency_graph()
        assert len(graph["nodes"]) == 1
        assert len(graph["edges"]) == 1
        assert graph["edges"][0]["to"] == "s2"

    def test_metrics(self):
        catalog = ServiceCatalogService()
        metrics = catalog.get_catalog_metrics()
        assert "total_services" in metrics

    def test_singleton(self):
        s1 = get_service_catalog()
        s2 = get_service_catalog()
        assert s1 is s2


# === User Analytics Metrics Service Tests ===
from app.services.user_analytics_metrics_service import (
    EventType,
    UserAnalyticsMetricsService,
    UserSegment,
    get_user_analytics_service,
)


class TestUserAnalyticsMetricsService:
    def test_track_event(self):
        service = UserAnalyticsMetricsService()
        eid = service.track_event(1, EventType.PAGE_VIEW, "home")
        assert eid is not None
        assert len(service.events_buffer) == 1
        assert service.users[1]["total_events"] == 1

    def test_sessions(self):
        service = UserAnalyticsMetricsService()
        sid = service.start_session(1)
        assert sid in service.sessions

        service.track_event(1, EventType.CLICK, "btn", session_id=sid)
        assert service.sessions[sid].events == 1

        service.end_session(sid)
        assert service.sessions[sid].end_time is not None

    def test_engagement_metrics(self):
        service = UserAnalyticsMetricsService()
        service.track_event(1, EventType.PAGE_VIEW, "home")
        # Track another event to update end_time and duration
        service.track_event(
            1, EventType.CLICK, "btn", session_id=service.events_buffer[0].session_id
        )

        metrics = service.get_engagement_metrics()
        assert metrics.dau == 1
        assert metrics.avg_events_per_session > 0

    def test_conversion_metrics(self):
        service = UserAnalyticsMetricsService()
        service.track_event(1, EventType.PAGE_VIEW, "landing")
        service.track_event(1, EventType.CONVERSION, "signup")

        metrics = service.get_conversion_metrics("signup")
        assert metrics.total_conversions == 1
        assert metrics.conversion_rate == 1.0

    def test_retention_metrics(self):
        service = UserAnalyticsMetricsService()
        # Mock user joined 30 days ago
        service.users[1] = {
            "first_seen": datetime.now(UTC) - timedelta(days=30),
            "last_seen": datetime.now(UTC),
            "total_events": 1,
        }

        metrics = service.get_retention_metrics()
        # Since we mocked user 1 manually, logic depends on how get_retention_metrics queries users.
        # It queries self.users.
        assert metrics.cohort_size >= 1

    def test_nps(self):
        service = UserAnalyticsMetricsService()
        service.record_nps_response(1, 10)  # Promoter
        service.record_nps_response(2, 0)  # Detractor

        metrics = service.get_nps_metrics()
        assert metrics.total_responses == 2
        assert metrics.promoters_percent == 50.0
        assert metrics.detractors_percent == 50.0
        assert metrics.nps_score == 0.0

    def test_ab_test(self):
        service = UserAnalyticsMetricsService()
        tid = service.create_ab_test("test1", ["A", "B"])
        variant = service.assign_variant(tid, 1)
        assert variant in ["A", "B"]

        service.record_ab_conversion(tid, 1)
        results = service.get_ab_test_results(tid)
        assert results.test_name == "test1"

    def test_segmentation(self):
        service = UserAnalyticsMetricsService()
        # New user
        service.users[1] = {
            "first_seen": datetime.now(UTC),
            "last_seen": datetime.now(UTC),
            "total_events": 1,
        }
        segments = service.segment_users()
        assert 1 in segments[UserSegment.NEW]

    def test_export_summary(self):
        service = UserAnalyticsMetricsService()
        summary = service.export_metrics_summary()
        assert "engagement" in summary
        assert "conversion" in summary

    def test_singleton(self):
        s1 = get_user_analytics_service()
        s2 = get_user_analytics_service()
        assert s1 is s2
