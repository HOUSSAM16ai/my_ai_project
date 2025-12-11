# app/services/orchestration/application/self_healer.py
"""
Self Healer Service
===================
Single Responsibility: Self-healing and fault recovery.
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime
from typing import Protocol

from app.services.orchestration.domain.models import (
    Node,
    NodeState,
    Pod,
    PodPhase,
    SelfHealingEvent,
)


class PodRepository(Protocol):
    def get(self, pod_id: str) -> Pod | None: ...
    def get_all(self) -> list[Pod]: ...
    def get_by_node(self, node_id: str) -> list[Pod]: ...
    def save(self, pod: Pod) -> None: ...
    def delete(self, pod_id: str) -> None: ...


class NodeRepository(Protocol):
    def get(self, node_id: str) -> Node | None: ...
    def get_all(self) -> list[Node]: ...
    def update(self, node: Node) -> None: ...


class HealingEventRepository(Protocol):
    def save(self, event: SelfHealingEvent) -> None: ...
    def get_recent(self, limit: int) -> list[SelfHealingEvent]: ...


class PodScheduler(Protocol):
    def schedule_pod(self, **kwargs) -> str: ...


class SelfHealer:
    """
    Self-healing orchestrator.
    
    Responsibilities:
    - Monitor pod health
    - Restart failed pods
    - Evacuate unhealthy nodes
    - Record healing events
    """
    
    def __init__(
        self,
        pod_repository: PodRepository,
        node_repository: NodeRepository,
        healing_event_repository: HealingEventRepository,
        pod_scheduler: PodScheduler,
    ):
        self._pod_repo = pod_repository
        self._node_repo = node_repository
        self._event_repo = healing_event_repository
        self._scheduler = pod_scheduler
    
    def check_and_heal_pods(self) -> list[str]:
        """Check all pods and heal failed ones"""
        healed_pods = []
        
        for pod in self._pod_repo.get_all():
            if self._is_pod_unhealthy(pod):
                if self._heal_pod(pod):
                    healed_pods.append(pod.pod_id)
        
        return healed_pods
    
    def check_and_heal_nodes(self) -> list[str]:
        """Check all nodes and evacuate unhealthy ones"""
        evacuated_nodes = []
        
        for node in self._node_repo.get_all():
            if self._is_node_unhealthy(node):
                if self._evacuate_node(node):
                    evacuated_nodes.append(node.node_id)
        
        return evacuated_nodes
    
    def _is_pod_unhealthy(self, pod: Pod) -> bool:
        """Check if pod is unhealthy"""
        # Simulate health check (in production: actual health probes)
        if pod.phase == PodPhase.FAILED:
            return True
        
        # Random failures for testing
        return random.random() < 0.01  # 1% failure rate
    
    def _is_node_unhealthy(self, node: Node) -> bool:
        """Check if node is unhealthy"""
        # Check heartbeat timeout
        time_since_heartbeat = (datetime.utcnow() - node.last_heartbeat).total_seconds()
        
        if time_since_heartbeat > 60:  # 60 seconds timeout
            return True
        
        # Check resource pressure
        if node.cpu_utilization > 95 or node.memory_utilization > 95:
            return True
        
        return False
    
    def _heal_pod(self, pod: Pod) -> bool:
        """Heal failed pod"""
        try:
            # Delete failed pod
            self._pod_repo.delete(pod.pod_id)
            
            # Reschedule pod
            new_pod_id = self._scheduler.schedule_pod(
                name=pod.name,
                namespace=pod.namespace,
                container_image=pod.container_image,
                cpu_request=pod.cpu_request,
                memory_request=pod.memory_request,
                cpu_limit=pod.cpu_limit,
                memory_limit=pod.memory_limit,
                labels=pod.labels,
            )
            
            # Record healing event
            self._record_healing_event(
                event_type="pod_restart",
                resource_id=pod.pod_id,
                details={"new_pod_id": new_pod_id, "reason": "health_check_failed"},
                success=True,
            )
            
            return True
        
        except Exception as e:
            self._record_healing_event(
                event_type="pod_restart",
                resource_id=pod.pod_id,
                details={"error": str(e)},
                success=False,
            )
            return False
    
    def _evacuate_node(self, node: Node) -> bool:
        """Evacuate pods from unhealthy node"""
        try:
            # Mark node as cordoned
            node.state = NodeState.CORDONED
            self._node_repo.update(node)
            
            # Get all pods on node
            pods = self._pod_repo.get_by_node(node.node_id)
            
            # Reschedule all pods
            rescheduled_count = 0
            for pod in pods:
                try:
                    self._pod_repo.delete(pod.pod_id)
                    self._scheduler.schedule_pod(
                        name=pod.name,
                        namespace=pod.namespace,
                        container_image=pod.container_image,
                        cpu_request=pod.cpu_request,
                        memory_request=pod.memory_request,
                        cpu_limit=pod.cpu_limit,
                        memory_limit=pod.memory_limit,
                        labels=pod.labels,
                    )
                    rescheduled_count += 1
                except Exception:
                    pass
            
            # Record healing event
            self._record_healing_event(
                event_type="node_evacuation",
                resource_id=node.node_id,
                details={
                    "total_pods": len(pods),
                    "rescheduled": rescheduled_count,
                },
                success=True,
            )
            
            return True
        
        except Exception as e:
            self._record_healing_event(
                event_type="node_evacuation",
                resource_id=node.node_id,
                details={"error": str(e)},
                success=False,
            )
            return False
    
    def _record_healing_event(
        self,
        event_type: str,
        resource_id: str,
        details: dict,
        success: bool,
    ) -> None:
        """Record healing event"""
        event_id = hashlib.sha256(
            f"{event_type}{resource_id}{time.time_ns()}".encode()
        ).hexdigest()[:16]
        
        event = SelfHealingEvent(
            event_id=event_id,
            event_type=event_type,
            resource_id=resource_id,
            timestamp=datetime.utcnow(),
            details=details,
            success=success,
        )
        
        self._event_repo.save(event)
    
    def get_healing_events(self, limit: int = 100) -> list[SelfHealingEvent]:
        """Get recent healing events"""
        return self._event_repo.get_recent(limit)
