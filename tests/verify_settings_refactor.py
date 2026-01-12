import os
import sys

# Ensure root is in path
sys.path.append(os.getcwd())

try:
    from microservices.memory_agent.settings import get_settings as get_mem_settings
    from microservices.orchestrator_service.settings import get_settings as get_orch_settings
    from microservices.planning_agent.settings import get_settings as get_plan_settings
except ImportError as e:
    print(f"Import Error: {e}")
    # Try to simulate how it might run if app is not found (though sys.path.append should fix it)
    sys.exit(1)


def verify():
    print("Verifying settings refactor...")

    # Orchestrator
    orch = get_orch_settings()
    assert orch.ENVIRONMENT == "development", f"Expected development, got {orch.ENVIRONMENT}"
    assert "orchestrator.db" in orch.DATABASE_URL
    assert orch.SERVICE_NAME == "orchestrator-service"
    print("Orchestrator settings: OK")

    # Planning
    plan = get_plan_settings()
    assert plan.ENVIRONMENT == "development"
    assert "planning_agent.db" in plan.DATABASE_URL
    assert plan.SERVICE_NAME == "planning-agent"
    print("Planning settings: OK")

    # Memory
    mem = get_mem_settings()
    assert mem.ENVIRONMENT == "development"
    assert "memory_agent.db" in mem.DATABASE_URL
    assert mem.SERVICE_NAME == "memory-agent"
    print("Memory settings: OK")


if __name__ == "__main__":
    verify()
