import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.services.agent_tools.domain.metrics import get_project_metrics_handler


async def test_handler():
    print("Testing get_project_metrics_handler...")
    metrics = await get_project_metrics_handler()
    print("Metrics Result:", metrics)


if __name__ == "__main__":
    asyncio.run(test_handler())
