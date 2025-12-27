
from unittest.mock import MagicMock, patch

import pytest

# We need to ensure we patch BEFORE import or patch the imported name in factory_core
# The problem might be that instantiate_all_planners is imported as a function
# so patching "app.services.overmind.planning.factory_core.instantiate_all_planners"
# should work if the test file imports factory_core directly.
from app.services.overmind.planning import factory_core
from app.services.overmind.planning.base_planner import BasePlanner
from app.services.overmind.planning.exceptions import NoActivePlannersError, PlannerNotFound
from app.services.overmind.planning.factory_core import (
    _GLOBAL_FACTORY,
    FactoryState,
    PlannerFactory,
    PlannerRecord,
    a_get_planner,
    a_select_best_planner,
    diagnostics_json,
    diagnostics_report,
    export_diagnostics,
    get_all_planners,
    instantiation_profiles,
    list_planner_metadata,
    list_quarantined,
    selection_profiles,
)


# Mock BasePlanner subclass for testing
class MockPlanner(BasePlanner):
    def __init__(self, name="mock_planner"):
        self._name = name

    @property
    def name(self):
        return self._name

    async def create_plan(self, objective, context=None):
        return {}

class AnotherMockPlanner(BasePlanner):
    name = "another_mock_planner"
    async def create_plan(self, objective, context=None):
        return {}

@pytest.fixture
def planner_factory():
    """Returns a fresh PlannerFactory instance."""
    return PlannerFactory()

@pytest.fixture
def mock_planner_instance():
    return MockPlanner()

class TestPlannerFactory:

    def test_initialization(self, planner_factory):
        assert isinstance(planner_factory._state, FactoryState)
        assert planner_factory._state.discovered is False
        assert planner_factory._state.discovery_runs == 0

    def test_discover_basic(self, planner_factory):
        # We need to mock importlib to simulate finding a package
        with patch("importlib.import_module") as mock_import:
            # Setup mock module structure
            mock_pkg = MagicMock()
            mock_pkg.__path__ = ["/fake/path"]
            mock_pkg.__name__ = "app.services.overmind.planning.generators"
            mock_import.return_value = mock_pkg

            with patch("pkgutil.walk_packages", return_value=[]):
                 # Try patching on the module object directly to be absolutely sure
                 with patch.object(factory_core, "instantiate_all_planners", return_value=[MockPlanner("mock_planner")]) as mock_instantiate:
                    planner_factory.discover()

                    mock_instantiate.assert_called()
                    assert planner_factory._state.discovered is True
                    assert planner_factory._state.discovery_runs == 1
                    # Ensure the MockPlanner was registered
                    assert "mock_planner" in planner_factory._state.planner_records
                    assert "mock_planner" in planner_factory._instance_cache

    def test_discover_with_force(self, planner_factory):
        planner_factory._state.discovered = True
        planner_factory._state.discovery_runs = 1

        with patch("app.services.overmind.planning.factory_core.instantiate_all_planners", return_value=[]):
            planner_factory.discover(force=True)
            assert planner_factory._state.discovery_runs == 2

    def test_register_planner_instance(self, planner_factory):
        p = MockPlanner(name="test_p")
        planner_factory._register_planner_instance(p)

        assert "test_p" in planner_factory._state.planner_records
        assert planner_factory._instance_cache["test_p"] == p
        record = planner_factory._state.planner_records["test_p"]
        assert record.instantiated is True

    def test_get_planner_cached(self, planner_factory):
        p = MockPlanner(name="cached_p")
        planner_factory._instance_cache["cached_p"] = p

        retrieved = planner_factory.get_planner("cached_p")
        assert retrieved == p

    def test_get_planner_not_found(self, planner_factory):
        with pytest.raises(PlannerNotFound):
            planner_factory.get_planner("non_existent")

    def test_get_planner_dynamic_instantiation(self, planner_factory):
        with patch.object(BasePlanner, "get_planner_class", return_value=MockPlanner):
            p = planner_factory.get_planner("mock_planner")
            assert isinstance(p, MockPlanner)
            assert "mock_planner" in planner_factory._instance_cache

    def test_list_planners(self, planner_factory):
        p1 = MockPlanner(name="p1")
        p2 = MockPlanner(name="p2")
        planner_factory._register_planner_instance(p1)
        planner_factory._register_planner_instance(p2)

        # Mark p2 as quarantined via record manipulation
        planner_factory._state.planner_records["p2"].quarantined = True

        assert planner_factory.list_planners() == ["p1"]
        assert "p2" in planner_factory.list_planners(include_quarantined=True)

    def test_select_best_planner_no_active(self, planner_factory):
        with patch.object(planner_factory, "discover"):
            with pytest.raises(NoActivePlannersError):
                planner_factory.select_best_planner("objective")

    def test_select_best_planner_success(self, planner_factory):
        p = MockPlanner(name="best_p")
        planner_factory._register_planner_instance(p)

        with patch("app.services.overmind.planning.factory_core.rank_planners", return_value=[(1.0, "best_p", None)]):
            selected = planner_factory.select_best_planner("objective")
            assert selected == p

    def test_self_heal(self, planner_factory):
        with patch.object(planner_factory, "discover") as mock_discover:
            result = planner_factory.self_heal()
            assert result["status"] == "healed"
            mock_discover.assert_called_with(force=True)

    def test_planner_stats(self, planner_factory):
        stats = planner_factory.planner_stats()
        assert "discovered" in stats
        assert "active_count" in stats

    def test_describe_planner(self, planner_factory):
        p = MockPlanner(name="desc_p")
        planner_factory._register_planner_instance(p)
        desc = planner_factory.describe_planner("desc_p")
        assert desc["name"] == "desc_p"

    def test_describe_planner_empty(self, planner_factory):
        assert planner_factory.describe_planner("none") == {}

    def test_health_check(self, planner_factory):
        p = MockPlanner(name="h_p")
        planner_factory._register_planner_instance(p)

        health = planner_factory.health_check(min_required=1)
        assert health["healthy"] is True

    def test_reload_planners(self, planner_factory):
        p = MockPlanner(name="r_p")
        planner_factory._register_planner_instance(p)

        with patch.object(planner_factory, "discover") as mock_discover:
            planner_factory.reload_planners()
            assert len(planner_factory._instance_cache) == 0
            mock_discover.assert_called_with(force=True)

    def test_select_strategy(self):
        s1 = PlannerFactory.select_strategy("simple objective")
        assert s1.name == "linear_strategy"

        s2 = PlannerFactory.select_strategy("very complex objective with many words > 50 ... " * 10)
        assert s2.name == "recursive_strategy" # Assuming complexity check passes

        mock_ctx = MagicMock()
        mock_ctx.constraints = {"fast_mode": True}
        s3 = PlannerFactory.select_strategy("obj", context=mock_ctx)
        assert s3.name == "linear_strategy"

class TestGlobalFunctions:
    """Tests for the global wrapper functions."""

    def setup_method(self):
        # Reset global factory state
        _GLOBAL_FACTORY._state = FactoryState()
        _GLOBAL_FACTORY._instance_cache = {}

    def test_get_all_planners(self):
        # Note: factory_core.list_planners is imported from local
        # BUT factory_core.get_all_planners calls list_planners internally
        # which refers to _GLOBAL_FACTORY.
        # We need to ensure _GLOBAL_FACTORY has data.

        p1 = MockPlanner("p1")
        _GLOBAL_FACTORY._register_planner_instance(p1)

        planners = get_all_planners(auto_instantiate=True)
        assert len(planners) == 1
        assert planners[0].name == "p1"

    def test_diagnostics(self):
        json_out = diagnostics_json()
        assert "version" in json_out

        report = diagnostics_report()
        assert "Diagnostics:" in report

    @patch("pathlib.Path.write_text")
    def test_export_diagnostics(self, mock_write):
        export_diagnostics("test.json")
        mock_write.assert_called()

    def test_list_quarantined(self):
        # Manually inject a quarantined record
        rec = PlannerRecord("q_p", "mod", quarantined=True)
        _GLOBAL_FACTORY._state.planner_records["q_p"] = rec

        assert "q_p" in list_quarantined()

    @pytest.mark.asyncio
    async def test_async_wrappers(self):
        p1 = MockPlanner("async_p")
        _GLOBAL_FACTORY._register_planner_instance(p1)

        p = await a_get_planner("async_p")
        assert p.name == "async_p"

        # mocking rank_planners
        with patch("app.services.overmind.planning.factory_core.rank_planners", return_value=[(1.0, "async_p", None)]):
            p = await a_select_best_planner("obj")
            assert p.name == "async_p"

    def test_telemetry_wrappers(self):
        # Just ensure they run without error
        assert isinstance(selection_profiles(), list)
        assert isinstance(instantiation_profiles(), list)
        assert isinstance(list_planner_metadata(), dict)
