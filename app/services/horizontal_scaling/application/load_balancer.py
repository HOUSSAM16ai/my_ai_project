"""
Load Balancer Implementation
============================

Core logic for load balancing algorithms.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from ..domain.models import Server, LoadBalancingAlgorithm, RegionZone


@dataclass
class LoadBalancerConfig:
    """Configuration for a load balancer instance."""
    lb_id: str
    name: str
    algorithm: LoadBalancingAlgorithm
    virtual_nodes: int = 150  # For Consistent Hashing


class LoadBalancerStrategy:
    """Implements load balancing algorithms."""

    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: List[Server] = []
        self.hash_ring: Dict[int, str] = {}
        self.current_index: int = 0  # For Round Robin
        self.total_requests: int = 0
        self.total_errors: int = 0

    def add_server(self, server: Server) -> None:
        """Add a server to the pool."""
        if server not in self.servers:
            self.servers.append(server)
            if self.config.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
                self._build_hash_ring()

    def remove_server(self, server_id: str) -> None:
        """Remove a server from the pool."""
        self.servers = [s for s in self.servers if s.server_id != server_id]
        if self.config.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
            self._build_hash_ring()

    def select_server(
        self,
        request_key: Optional[str] = None,
        client_region: Optional[RegionZone] = None,
    ) -> Optional[Server]:
        """Select a server based on the configured algorithm."""

        # Filter available servers
        available_servers = [s for s in self.servers if s.is_available]
        if not available_servers:
            return None

        algo = self.config.algorithm

        if algo == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin(available_servers)
        elif algo == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections(available_servers)
        elif algo == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(available_servers)
        elif algo == LoadBalancingAlgorithm.LATENCY_BASED:
            return self._latency_based(available_servers)
        elif algo == LoadBalancingAlgorithm.CONSISTENT_HASH:
            return self._consistent_hash(request_key or "")
        elif algo == LoadBalancingAlgorithm.GEOGRAPHIC:
            return self._geographic_routing(available_servers, client_region)
        else:
            return self._intelligent_routing(available_servers)

    def _build_hash_ring(self) -> None:
        """Rebuild the hash ring for consistent hashing."""
        self.hash_ring.clear()
        for server in self.servers:
            for i in range(self.config.virtual_nodes):
                virtual_key = f"{server.server_id}:{i}"
                hash_value = int(hashlib.md5(virtual_key.encode()).hexdigest(), 16)
                self.hash_ring[hash_value] = server.server_id

    def _round_robin(self, servers: List[Server]) -> Server:
        self.current_index = (self.current_index + 1) % len(servers)
        return servers[self.current_index]

    def _least_connections(self, servers: List[Server]) -> Server:
        return min(servers, key=lambda s: s.active_connections)

    def _weighted_round_robin(self, servers: List[Server]) -> Server:
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return servers[0]

        rand_val = random.uniform(0, total_weight)
        cumulative = 0.0
        for server in servers:
            cumulative += server.weight
            if cumulative >= rand_val:
                return server
        return servers[-1]

    def _latency_based(self, servers: List[Server]) -> Server:
        return min(servers, key=lambda s: s.avg_latency_ms)

    def _consistent_hash(self, key: str) -> Optional[Server]:
        if not self.hash_ring:
            return None

        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        sorted_hashes = sorted(self.hash_ring.keys())

        for hash_val in sorted_hashes:
            if hash_val >= key_hash:
                server_id = self.hash_ring[hash_val]
                # Find the server object from ID
                return next((s for s in self.servers if s.server_id == server_id), None)

        # Wrap around
        first_hash = sorted_hashes[0]
        server_id = self.hash_ring[first_hash]
        return next((s for s in self.servers if s.server_id == server_id), None)

    def _geographic_routing(self, servers: List[Server], client_region: Optional[RegionZone]) -> Server:
        if client_region:
            region_servers = [s for s in servers if s.region == client_region]
            if region_servers:
                return min(region_servers, key=lambda s: s.active_connections)
        return min(servers, key=lambda s: s.active_connections)

    def _intelligent_routing(self, servers: List[Server]) -> Server:
        def score_server(s: Server) -> float:
            connection_score = 1.0 - (s.active_connections / max(s.max_connections, 1))
            cpu_score = 1.0 - (s.cpu_usage / 100.0)
            memory_score = 1.0 - (s.memory_usage / 100.0)
            latency_score = max(0, 1.0 - (s.avg_latency_ms / 1000.0))
            error_score = 1.0 - (s.total_errors / max(s.total_requests, 1))

            weights = {
                "connections": 0.3,
                "cpu": 0.2,
                "memory": 0.2,
                "latency": 0.2,
                "errors": 0.1,
            }

            return (
                weights["connections"] * connection_score
                + weights["cpu"] * cpu_score
                + weights["memory"] * memory_score
                + weights["latency"] * latency_score
                + weights["errors"] * error_score
            )

        return max(servers, key=score_server)
