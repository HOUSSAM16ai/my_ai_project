
import sys
import os

# Ensure the app path is in sys.path
sys.path.append(os.getcwd())

def verify_refactor():
    print("🔍 Verifying 'Wave 8' Refactoring (AI Project Management)...")

    try:
        # 1. Test Import from Shim
        from app.services.ai_project_management import ProjectOrchestrator, Task, TeamMember, TaskPriority, TaskStatus
        print("✅ Shim imports successful.")

        # 2. Test Import from New Structure
        from app.services.ai_project_management.facade import ProjectOrchestrator as PO2
        print("✅ Facade imports successful.")

        # 3. Test Functionality
        orchestrator = ProjectOrchestrator()

        dev = TeamMember(member_id="d1", name="Test Dev", role="Dev", skills=["python"])
        orchestrator.add_team_member(dev)

        task = Task(
            task_id="t1",
            title="Refactor",
            description="Test",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            estimated_hours=10,
            tags=["python"]
        )
        orchestrator.add_task(task)

        insights = orchestrator.generate_smart_insights()

        assert "project_health" in insights
        print("✅ Functionality test passed (Insights generated).")

        print("\n🚀 VERIFICATION SUCCESSFUL: Wave 8 Complete.")

    except ImportError as e:
        print(f"❌ ImportError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Runtime Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_refactor()
