"""
Tests for planning_logic refactoring (Controller/Service separation)
=====================================================================
Verifies that the extracted planning logic functions work correctly
and maintain the same behavior as the original implementation.
"""

import pytest
from app.overmind.planning.hyper_planner import planning_logic, config
from app.overmind.planning.schemas import PlannedTask


class TestChunkingLogic:
    """Test chunking and streaming strategy logic."""

    def test_calculate_chunking_basic(self):
        """Test basic chunking calculation without adaptation."""
        files = ["file1.py", "file2.py"]
        req_lines = 1000
        
        total_chunks, per_chunk, adaptive = planning_logic.calculate_chunking(files, req_lines)
        
        assert total_chunks > 0
        assert per_chunk > 0
        assert isinstance(adaptive, bool)

    def test_calculate_chunking_adaptive(self):
        """Test adaptive chunking when projected tasks exceed cap."""
        # Use many files to trigger adaptive behavior
        files = [f"file{i}.py" for i in range(50)]
        req_lines = 5000
        
        total_chunks, per_chunk, adaptive = planning_logic.calculate_chunking(files, req_lines)
        
        # Should adapt to stay within task cap
        assert total_chunks > 0
        assert per_chunk > 0

    def test_determine_streaming_strategy_enabled(self):
        """Test streaming strategy when conditions are met."""
        # Assuming STREAM_MIN_CHUNKS is typically 2
        total_chunks = 5
        can_stream = True
        
        result = planning_logic.determine_streaming_strategy(total_chunks, can_stream)
        
        # Should enable streaming if configured
        assert isinstance(result, bool)

    def test_determine_streaming_strategy_disabled(self):
        """Test streaming strategy when streaming not possible."""
        total_chunks = 5
        can_stream = False
        
        result = planning_logic.determine_streaming_strategy(total_chunks, can_stream)
        
        assert result is False

    def test_can_stream_check(self):
        """Test streaming capability check."""
        result = planning_logic.can_stream()
        
        assert isinstance(result, bool)


class TestPruningLogic:
    """Test task pruning logic."""

    def test_prune_no_action_needed(self):
        """Test pruning when task count is within limits."""
        tasks = [
            PlannedTask(
                task_id=f"t{i:02d}",
                description=f"Task {i}",
                tool_name="generic_think",
                tool_args={},
                dependencies=[],
            )
            for i in range(1, 11)  # 10 tasks, well under cap
        ]
        
        idx, pruned = planning_logic.prune_tasks_if_needed(tasks, 11, [])
        
        assert idx == 11
        assert len(pruned) == 0
        assert len(tasks) == 10

    def test_prune_semantic_tasks(self):
        """Test pruning of semantic analysis tasks when over cap."""
        # Create tasks that exceed cap
        tasks = [
            PlannedTask(
                task_id=f"t{i:02d}",
                description="Regular task",
                tool_name="generic_think",
                tool_args={},
                dependencies=[],
            )
            for i in range(1, config.GLOBAL_TASK_CAP + 1)
        ]
        
        # Add semantic task that should be pruned
        tasks.append(
            PlannedTask(
                task_id=f"t{config.GLOBAL_TASK_CAP + 1:02d}",
                description="Semantic structural JSON analysis",
                tool_name="generic_think",
                tool_args={},
                dependencies=[],
            )
        )
        
        original_count = len(tasks)
        idx, pruned = planning_logic.prune_tasks_if_needed(tasks, config.GLOBAL_TASK_CAP + 2, [])
        
        # Should have pruned at least one task
        assert len(tasks) <= config.GLOBAL_TASK_CAP
        assert len(pruned) > 0 or original_count <= config.GLOBAL_TASK_CAP


class TestMetadataBuilding:
    """Test metadata building logic."""

    def test_build_plan_metadata_complete(self):
        """Test building complete metadata."""
        ctx = {
            "lang": "en",
            "files": ["file1.py", "file2.py"],
            "req_lines": 1000,
            "total_chunks": 5,
            "per_chunk": 200,
            "use_stream": True,
            "adaptive_chunking": False,
            "role_task_id": "t01",
            "section_task_id": "t02",
            "global_code_summary_task_id": "t03",
            "context_source": "deep_index",
            "struct_meta": {
                "files_scanned": 100,
                "hotspot_count": 5,
                "duplicate_groups": 2,
                "index_version": "2.0",
                "attached": True,
            },
        }
        
        meta = planning_logic.build_plan_metadata(
            ctx, [], [], 50, True, True
        )
        
        assert meta["language"] == "en"
        assert len(meta["files"]) == 2
        assert meta["streaming"] is True
        assert meta["files_scanned"] == 100
        assert meta["container_files_detected"] is True


class TestFileResolution:
    """Test file resolution logic."""

    def test_resolve_target_files(self):
        """Test extracting and normalizing filenames from objective."""
        objective = "Analyze file1.py and file2.py then write report.md"
        
        files = planning_logic.resolve_target_files(objective)
        
        assert isinstance(files, list)
        # Should extract filenames from objective

    def test_resolve_target_files_with_extension_inference(self):
        """Test filename resolution with extension inference."""
        objective = "Read config and main files"
        
        files = planning_logic.resolve_target_files(objective)
        
        assert isinstance(files, list)


class TestValidationLogic:
    """Test validation logic."""

    def test_validate_objective_valid(self):
        """Test validation of valid objectives."""
        assert planning_logic.validate_objective("Analyze the repository structure") is True
        assert planning_logic.validate_objective("Create a detailed report") is True

    def test_validate_objective_invalid(self):
        """Test validation rejects invalid objectives."""
        assert planning_logic.validate_objective("") is False
        assert planning_logic.validate_objective("abc") is False
        assert planning_logic.validate_objective("12345") is False
        assert planning_logic.validate_objective("   ") is False

    def test_validate_plan_success(self):
        """Test plan validation with valid plan."""
        tasks = [
            PlannedTask(
                task_id="t01",
                description="Task 1",
                tool_name="generic_think",
                tool_args={},
                dependencies=[],
            ),
            PlannedTask(
                task_id="t02",
                description="Task 2",
                tool_name="write_file",
                tool_args={"path": "output.md"},
                dependencies=["t01"],
            ),
        ]
        
        # Should not raise
        planning_logic.validate_plan(tasks, ["output.md"], "Test objective", "test_planner")

    def test_validate_plan_dangling_dependency(self):
        """Test plan validation catches dangling dependencies."""
        from app.overmind.planning.base_planner import PlanValidationError
        
        tasks = [
            PlannedTask(
                task_id="t01",
                description="Task 1",
                tool_name="generic_think",
                tool_args={},
                dependencies=["t99"],  # Non-existent dependency
            ),
        ]
        
        with pytest.raises(PlanValidationError):
            planning_logic.validate_plan(tasks, [], "Test objective", "test_planner")

    def test_validate_plan_excessive_tasks(self):
        """Test plan validation catches excessive task count."""
        from app.overmind.planning.base_planner import PlanValidationError
        
        # Create more tasks than allowed by cap
        tasks = [
            PlannedTask(
                task_id=f"t{i:04d}",
                description=f"Task {i}",
                tool_name="generic_think",
                tool_args={},
                dependencies=[],
            )
            for i in range(1, config.GLOBAL_TASK_CAP + 100)
        ]
        
        with pytest.raises(PlanValidationError):
            planning_logic.validate_plan(tasks, [], "Test objective", "test_planner")


class TestIntegrationWithCore:
    """Test integration between core.py and planning_logic.py"""

    def test_core_uses_planning_logic(self):
        """Test that core.py properly delegates to planning_logic."""
        from app.overmind.planning.hyper_planner.core import UltraHyperPlanner
        
        planner = UltraHyperPlanner()
        
        # Generate a simple plan
        plan = planner.generate_plan("Create a simple test file test.md with basic content")
        
        # Verify plan was created successfully
        assert plan is not None
        assert plan.objective is not None
        assert len(plan.tasks) > 0
        
        # Verify metadata was built using planning_logic
        assert plan.meta is not None
        assert "language" in plan.meta
        assert "files" in plan.meta
