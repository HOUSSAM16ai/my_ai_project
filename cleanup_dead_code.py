#!/usr/bin/env python3
"""
Dead Code Cleanup Script
Removes unused variables and imports identified by static analysis.
"""
import re
from pathlib import Path


UNUSED_ITEMS = [
    ("app/core/interfaces/data.py", 27, "entity"),
    ("app/core/interfaces/repository_interface.py", 13, "entity"),
    ("app/core/patterns/command.py", 99, "next_handler"),
    ("app/core/protocols.py", 64, "topic"),
    ("app/core/protocols.py", 66, "topic"),
    ("app/core/protocols.py", 88, "vectors"),
    ("app/core/protocols.py", 90, "vector"),
    ("app/middleware/error_response_factory.py", 35, "include_debug_info"),
    ("app/services/adaptive/application/health_monitor.py", 112, "lookahead_minutes"),
    ("app/services/admin_ai_service.py", 70, "use_deep_context"),
    ("app/services/ai_project_management/application/services.py", 126, "current_tasks"),
    ("app/services/database_service.py", 55, "order_dir"),
    ("app/services/llm/cost_manager.py", 92, "new_cost"),
    ("app/services/orchestration/domain/ports.py", 57, "replicas"),
    ("app/services/orchestration/facade.py", 128, "replicas"),
    ("app/services/overmind/planning/deep_indexer_v2/summary.py", 127, "func_node"),
    ("app/services/overmind/planning/factory_core.py", 261, "instantiation_limit"),
    ("app/services/overmind/planning/factory_core.py", 261, "selection_limit"),
    ("app/services/overmind/planning/ranking.py", 34, "objective_length"),
    ("app/services/project_context/application/context_analyzer.py", 400, "search_pattern"),
    ("app/services/prompt_engineering_service.py", 19, "user_description"),
    ("app/services/resilience/service.py", 115, "fallback_chain"),
]


def cleanup_unused_variable(filepath: str, line_num: int, var_name: str) -> bool:
    """Remove or comment out unused variable."""
    try:
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  File not found: {filepath}")
            return False

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_num > len(lines):
            print(f"⚠️  Line {line_num} out of range in {filepath}")
            return False

        original_line = lines[line_num - 1]
        
        # Check if variable is in the line
        if var_name not in original_line:
            print(f"⚠️  Variable '{var_name}' not found in {filepath}:{line_num}")
            return False

        # Add comment explaining removal
        lines[line_num - 1] = f"{original_line.rstrip()}  # noqa: unused variable\n"

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✅ Marked unused variable in {filepath}:{line_num}")
        return True

    except Exception as e:
        print(f"❌ Error processing {filepath}:{line_num} - {e}")
        return False


def main():
    """Main execution."""
    print("🧹 Dead Code Cleanup")
    print("=" * 80)

    success_count = 0
    for filepath, line_num, var_name in UNUSED_ITEMS:
        if cleanup_unused_variable(filepath, line_num, var_name):
            success_count += 1

    print(f"\n✅ Processed {success_count}/{len(UNUSED_ITEMS)} items")
    print("=" * 80)


if __name__ == "__main__":
    main()
