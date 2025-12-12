"""
Horizontal Scaling Manager
==========================

Orchestrates the scaling logic, health checks, and metrics analysis.
"""
from __future__ import annotations

import random
import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from ..domain.models import (
    LoadBalancingAlgorithm,
    RegionZone,
    ScalingEvent,
    ScalingMetrics,
    Server,
    ServerState,
)
from .load_balancer import LoadBalancerConfig, LoadBalancerStrategy


class HorizontalScalingManager:
    """
    Main orchestrator for horizontal scaling.
    Manages load balancers, servers, and scaling decisions.
    """

    def __init__(self):
        self.load_balancers: Dict[str, LoadBalancerStrategy] = {}
        self.servers: Dict[str, Server] = {}
        self.metrics_history: deque[ScalingMetrics] = deque(maxlen=1000)
        self.scaling_policy: Dict[str, Any] = {
            "min_servers": 10,
            "max_servers": 1000,
            "target_cpu": 70.0,
            "target_memory": 75.0,
            "target_latency_ms": 200.0,
            "scale_up_threshold": 80.0,
            "scale_down_threshold": 30.0,
            "cooldown_seconds": 300,
        }
        self.last_scaling_event: Optional[datetime] = None
        self._lock = threading.Lock()

    def create_load_balancer(
        self,
        lb_id: str,
        name: str,
        algorithm: LoadBalancingAlgorithm,
    ) -> LoadBalancerStrategy:
        """Create and register a new load balancer strategy."""
        config = LoadBalancerConfig(lb_id=lb_id, name=name, algorithm=algorithm)
        strategy = LoadBalancerStrategy(config)

        # Add existing servers to the new load balancer
        for server in self.servers.values():
            strategy.add_server(server)

        self.load_balancers[lb_id] = strategy
        return strategy

    def register_server(
        self,
        server_id: str,
        name: str,
        ip_address: str,
        port: int,
        region: RegionZone,
        weight: int = 100,
    ) -> Server:
        """Register a new server in the cluster."""
        server = Server(
            server_id=server_id,
            name=name,
            ip_address=ip_address,
            port=port,
            region=region,
            state=ServerState.HEALTHY,
            weight=weight,
        )
        with self._lock:
            self.servers[server_id] = server
            # Add to all existing load balancers
            for lb in self.load_balancers.values():
                lb.add_server(server)

        return server

    def route_request(
        self,
        lb_id: str,
        request_key: Optional[str] = None,
        client_region: Optional[RegionZone] = None,
    ) -> Optional[Server]:
        """Route a request to an appropriate server."""
        lb = self.load_balancers.get(lb_id)
        if not lb:
            return None
        return lb.select_server(request_key, client_region)

    def analyze_scaling_needs(self) -> ScalingEvent:
        """Analyze metrics and determine if scaling is needed."""
        if not self.servers:
            return ScalingEvent.NO_ACTION

        active_servers = [
            s for s in self.servers.values()
            if s.state in (ServerState.HEALTHY, ServerState.DEGRADED)
        ]

        if not active_servers:
            return ScalingEvent.NO_ACTION

        avg_cpu = sum(s.cpu_usage for s in active_servers) / len(active_servers)
        avg_memory = sum(s.memory_usage for s in active_servers) / len(active_servers)
        avg_latency = sum(s.avg_latency_ms for s in active_servers) / len(active_servers)

        # Check cooldown
        if self.last_scaling_event:
            elapsed = (datetime.now(UTC) - self.last_scaling_event).total_seconds()
            if elapsed < self.scaling_policy["cooldown_seconds"]:
                return ScalingEvent.NO_ACTION

        scale_up_threshold = self.scaling_policy["scale_up_threshold"]
        scale_down_threshold = self.scaling_policy["scale_down_threshold"]

        if (
            avg_cpu > scale_up_threshold
            or avg_memory > scale_up_threshold
            or avg_latency > self.scaling_policy["target_latency_ms"] * 2
        ):
            return ScalingEvent.SCALE_OUT
        elif (
            avg_cpu < scale_down_threshold
            and avg_memory < scale_down_threshold
            and len(active_servers) > self.scaling_policy["min_servers"]
        ):
            return ScalingEvent.SCALE_IN

        return ScalingEvent.NO_ACTION

    def execute_scaling(self, event: ScalingEvent, count: int = 1) -> List[Server]:
        """Execute the scaling action."""
        servers_affected = []

        if event == ScalingEvent.SCALE_OUT:
            for i in range(count):
                server_id = f"server-{len(self.servers) + i + 1}"
                server = self.register_server(
                    server_id=server_id,
                    name=f"Auto-scaled Server {server_id}",
                    ip_address=f"10.0.{(len(self.servers) + i) // 255}.{(len(self.servers) + i) % 255}",
                    port=8000 + i,
                    region=random.choice(list(RegionZone)),
                )
                servers_affected.append(server)
                # Note: register_server already adds to LBs

        elif event == ScalingEvent.SCALE_IN:
            # Remove least active servers
            servers_sorted = sorted(self.servers.values(), key=lambda s: s.active_connections)
            for i in range(min(count, len(servers_sorted))):
                server = servers_sorted[i]
                if server.active_connections == 0:
                    server.state = ServerState.DRAINING
                    servers_affected.append(server)

                    # Remove from LBs
                    for lb in self.load_balancers.values():
                        lb.remove_server(server.server_id)

        self.last_scaling_event = datetime.now(UTC)
        return servers_affected

    def health_check_all_servers(self) -> Dict[str, bool]:
        """Run health checks on all servers."""
        results = {}
        for server_id, server in self.servers.items():
            is_healthy = self._simulate_health_check(server)

            if is_healthy:
                if server.state != ServerState.HEALTHY:
                    server.state = ServerState.HEALTHY
            else:
                server.state = ServerState.UNHEALTHY

            server.last_health_check = datetime.now(UTC)
            results[server_id] = is_healthy

        return results

    def _simulate_health_check(self, server: Server) -> bool:
        """Simulate a health check (placeholder for real network call)."""
        return random.random() > 0.05

    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for the cluster."""
        active_servers = [
            s for s in self.servers.values()
            if s.state in (ServerState.HEALTHY, ServerState.DEGRADED)
        ]

        if not active_servers:
            return {
                "total_servers": len(self.servers),
                "active_servers": 0,
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
                "avg_latency_ms": 0.0,
                "total_connections": 0,
                "total_requests": 0,
            }

        return {
            "total_servers": len(self.servers),
            "active_servers": len(active_servers),
            "avg_cpu": sum(s.cpu_usage for s in active_servers) / len(active_servers),
            "avg_memory": sum(s.memory_usage for s in active_servers) / len(active_servers),
            "avg_latency_ms": sum(s.avg_latency_ms for s in active_servers) / len(active_servers),
            "total_connections": sum(s.active_connections for s in active_servers),
            "total_requests": sum(s.total_requests for s in active_servers),
            "load_balancers": len(self.load_balancers),
        }
