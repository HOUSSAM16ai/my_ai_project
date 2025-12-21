
from app.services.overmind.planning.hyper_planner import config, scan_logic
from app.services.overmind.planning.hyper_planner.steps.scan_step import ScanRepoStep


class TestScanLogicRefactor:
    """Verifies that the refactoring of ScanRepoStep and scan_logic preserves behavior."""

    def test_wants_repo_scan_detection(self):
        """Test the semantic detection of repository scan intent."""
        # Positive cases
        assert scan_logic.wants_repo_scan("Analyze the repository structure")
        assert scan_logic.wants_repo_scan("Give me a report on the architecture")
        assert scan_logic.wants_repo_scan("scan the repo please")
        assert scan_logic.wants_repo_scan("تحليل هيكل المشروع")  # Arabic support

        # Negative cases
        assert not scan_logic.wants_repo_scan("Write a python script to calculate pi")
        assert not scan_logic.wants_repo_scan("Hello world")

    def test_generate_repo_scan_tasks(self):
        """Test that tasks are generated correctly."""
        idx = 1
        deps = []

        # Mock config to ensure deterministic output if needed,
        # but the default config.CORE_READ_FILES should be stable enough.

        idx_new, tasks = scan_logic.generate_repo_scan_tasks(idx, deps)

        assert idx_new > idx
        assert len(tasks) > 0
        assert len(deps) == len(tasks)

        # Verify structure of generated tasks
        first_task = tasks[0]
        assert first_task.tool_name == config.TOOL_LIST
        assert first_task.task_id == "t01"

        # Check that we have read tasks
        read_tasks = [t for t in tasks if t.tool_name == config.TOOL_READ]
        assert len(read_tasks) > 0

    def test_scan_step_integration(self):
        """Test that the Step class correctly calls the logic."""
        step = ScanRepoStep()
        tasks = []
        context = {"objective": "Analyze repository architecture"}

        # Enable the feature flag for the test
        original_setting = config.ALLOW_LIST_READ_ANALYSIS
        config.ALLOW_LIST_READ_ANALYSIS = True

        try:
            next_idx = step.execute(tasks, 1, context)

            assert next_idx > 1
            assert len(tasks) > 0

            # Ensure dependencies were captured in context
            assert "analysis_dependency_ids" in context
            assert len(context["analysis_dependency_ids"]) == len(tasks)

        finally:
            config.ALLOW_LIST_READ_ANALYSIS = original_setting

    def test_scan_step_no_trigger(self):
        """Test that the Step does nothing if objective doesn't match."""
        step = ScanRepoStep()
        tasks = []
        context = {"objective": "Just write a poem"}

        step.execute(tasks, 1, context)

        # Should imply no repo scan tasks were added (idx stays same or increases only if extra files exist)
        # Assuming no extra files in this test env by default
        # But we can verify no TOOL_LIST tasks were added
        list_tasks = [t for t in tasks if t.tool_name == config.TOOL_LIST]
        assert len(list_tasks) == 0
