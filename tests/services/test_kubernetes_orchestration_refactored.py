
import pytest
import asyncio
from app.services.orchestration.domain import Pod, Node, NodeState, PodPhase
from app.services.orchestration.application.pod_scheduler import PodScheduler, PodRepository, NodeRepository
from typing import List, Optional

class MockPodRepository:
    def __init__(self):
        self.pods = {}

    def save(self, pod: Pod) -> None:
        self.pods[pod.pod_id] = pod

    def get(self, pod_id: str) -> Optional[Pod]:
        return self.pods.get(pod_id)

class MockNodeRepository:
    def __init__(self, nodes: List[Node]):
        self.nodes = {n.node_id: n for n in nodes}

    def get_all(self) -> List[Node]:
        return list(self.nodes.values())

    def update(self, node: Node) -> None:
        self.nodes[node.node_id] = node

@pytest.mark.asyncio
async def test_kubernetes_orchestration_imports():
    """
    Smoke test to verify that the refactored Kubernetes orchestration module
    can be imported and used without the legacy facade.
    """
    node = Node(
        node_id="node-1",
        name="worker-1",
        state=NodeState.READY,
        cpu_capacity=4.0,
        memory_capacity=8192.0
    )

    pod_repo = MockPodRepository()
    node_repo = MockNodeRepository([node])

    # Just verifying instantiation to ensure no import errors
    scheduler = PodScheduler(pod_repository=pod_repo, node_repository=node_repo)
    assert scheduler is not None

    # Try scheduling a pod
    pod_id = scheduler.schedule_pod(
        name="test-pod",
        namespace="default",
        container_image="nginx:latest"
    )
    assert pod_id is not None
    assert len(pod_repo.pods) == 1
    assert list(pod_repo.pods.values())[0].pod_id == pod_id
