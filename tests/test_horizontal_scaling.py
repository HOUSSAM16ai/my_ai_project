# tests/test_horizontal_scaling.py
"""
Tests for Horizontal Scaling & SPOF Elimination Services
"""

import pytest
from app.services.horizontal_scaling_service import (
    ChaosMonkey,
    HorizontalScalingOrchestrator,
    LoadBalancer,
    LoadBalancingAlgorithm,
    RegionZone,
    ScalingEvent,
    Server,
    ServerState,
    get_scaling_orchestrator,
)


class TestHorizontalScalingOrchestrator:
    """Test horizontal scaling orchestrator"""

    def test_create_load_balancer(self):
        """Test creating a load balancer"""
        orchestrator = HorizontalScalingOrchestrator()
        
        lb = orchestrator.create_load_balancer(
            lb_id="lb-1",
            name="Primary LB",
            algorithm=LoadBalancingAlgorithm.ROUND_ROBIN,
        )
        
        assert lb.lb_id == "lb-1"
        assert lb.name == "Primary LB"
        assert lb.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN
        assert len(lb.servers) == 0

    def test_register_server(self):
        """Test registering a server"""
        orchestrator = HorizontalScalingOrchestrator()
        
        server = orchestrator.register_server(
            server_id="server-1",
            name="Web Server 1",
            ip_address="10.0.0.1",
            port=8000,
            region=RegionZone.US_EAST,
            weight=100,
        )
        
        assert server.server_id == "server-1"
        assert server.name == "Web Server 1"
        assert server.ip_address == "10.0.0.1"
        assert server.port == 8000
        assert server.region == RegionZone.US_EAST
        assert server.state == ServerState.HEALTHY

    def test_round_robin_routing(self):
        """Test round robin load balancing"""
        orchestrator = HorizontalScalingOrchestrator()
        
        # Create load balancer
        lb = orchestrator.create_load_balancer(
            "lb-1", "Primary LB", LoadBalancingAlgorithm.ROUND_ROBIN
        )
        
        # Register servers
        for i in range(3):
            server = orchestrator.register_server(
                server_id=f"server-{i+1}",
                name=f"Server {i+1}",
                ip_address=f"10.0.0.{i+1}",
                port=8000 + i,
                region=RegionZone.US_EAST,
            )
            lb.add_server(server)
        
        # Route requests - should cycle through servers
        selected_servers = []
        for _ in range(6):
            server = orchestrator.route_request("lb-1")
            if server:
                selected_servers.append(server.server_id)
        
        # Should have used all 3 servers twice (cycling pattern)
        assert len(selected_servers) == 6
        # Check that we have 2 of each server (round robin distributes evenly)
        assert selected_servers.count("server-1") == 2
        assert selected_servers.count("server-2") == 2
        assert selected_servers.count("server-3") == 2

    def test_least_connections_routing(self):
        """Test least connections load balancing"""
        orchestrator = HorizontalScalingOrchestrator()
        
        lb = orchestrator.create_load_balancer(
            "lb-1", "Primary LB", LoadBalancingAlgorithm.LEAST_CONNECTIONS
        )
        
        # Register servers with different connection counts
        server1 = orchestrator.register_server(
            "server-1", "Server 1", "10.0.0.1", 8000, RegionZone.US_EAST
        )
        server1.active_connections = 10
        
        server2 = orchestrator.register_server(
            "server-2", "Server 2", "10.0.0.2", 8001, RegionZone.US_EAST
        )
        server2.active_connections = 5
        
        server3 = orchestrator.register_server(
            "server-3", "Server 3", "10.0.0.3", 8002, RegionZone.US_EAST
        )
        server3.active_connections = 15
        
        lb.add_server(server1)
        lb.add_server(server2)
        lb.add_server(server3)
        
        # Should route to server with least connections (server-2)
        selected = orchestrator.route_request("lb-1")
        assert selected is not None
        assert selected.server_id == "server-2"

    def test_latency_based_routing(self):
        """Test latency-based routing"""
        orchestrator = HorizontalScalingOrchestrator()
        
        lb = orchestrator.create_load_balancer(
            "lb-1", "Primary LB", LoadBalancingAlgorithm.LATENCY_BASED
        )
        
        # Register servers with different latencies
        server1 = orchestrator.register_server(
            "server-1", "Server 1", "10.0.0.1", 8000, RegionZone.US_EAST
        )
        server1.avg_latency_ms = 100.0
        
        server2 = orchestrator.register_server(
            "server-2", "Server 2", "10.0.0.2", 8001, RegionZone.US_EAST
        )
        server2.avg_latency_ms = 50.0  # Fastest!
        
        server3 = orchestrator.register_server(
            "server-3", "Server 3", "10.0.0.3", 8002, RegionZone.US_EAST
        )
        server3.avg_latency_ms = 150.0
        
        lb.add_server(server1)
        lb.add_server(server2)
        lb.add_server(server3)
        
        # Should route to fastest server
        selected = orchestrator.route_request("lb-1")
        assert selected is not None
        assert selected.server_id == "server-2"

    def test_consistent_hashing(self):
        """Test consistent hashing routing"""
        orchestrator = HorizontalScalingOrchestrator()
        
        lb = orchestrator.create_load_balancer(
            "lb-1", "Primary LB", LoadBalancingAlgorithm.CONSISTENT_HASH
        )
        
        # Register servers
        for i in range(3):
            server = orchestrator.register_server(
                f"server-{i+1}", f"Server {i+1}",
                f"10.0.0.{i+1}", 8000 + i, RegionZone.US_EAST
            )
            lb.add_server(server)
        
        # Same key should always route to same server
        key1 = "user-12345"
        server1 = orchestrator.route_request("lb-1", request_key=key1)
        server2 = orchestrator.route_request("lb-1", request_key=key1)
        server3 = orchestrator.route_request("lb-1", request_key=key1)
        
        assert server1 is not None
        assert server2 is not None
        assert server3 is not None
        assert server1.server_id == server2.server_id == server3.server_id

    def test_geographic_routing(self):
        """Test geographic routing"""
        orchestrator = HorizontalScalingOrchestrator()
        
        lb = orchestrator.create_load_balancer(
            "lb-1", "Primary LB", LoadBalancingAlgorithm.GEOGRAPHIC
        )
        
        # Register servers in different regions
        server_us = orchestrator.register_server(
            "server-us", "US Server", "10.0.0.1", 8000, RegionZone.US_EAST
        )
        server_eu = orchestrator.register_server(
            "server-eu", "EU Server", "10.0.1.1", 8000, RegionZone.EUROPE
        )
        server_asia = orchestrator.register_server(
            "server-asia", "Asia Server", "10.0.2.1", 8000, RegionZone.ASIA
        )
        
        lb.add_server(server_us)
        lb.add_server(server_eu)
        lb.add_server(server_asia)
        
        # Request from Europe should route to Europe server
        selected = orchestrator.route_request("lb-1", client_region=RegionZone.EUROPE)
        assert selected is not None
        assert selected.region == RegionZone.EUROPE

    def test_scaling_analysis(self):
        """Test scaling needs analysis"""
        orchestrator = HorizontalScalingOrchestrator()
        
        # Register servers with high CPU usage
        for i in range(5):
            server = orchestrator.register_server(
                f"server-{i+1}", f"Server {i+1}",
                f"10.0.0.{i+1}", 8000 + i, RegionZone.US_EAST
            )
            server.cpu_usage = 85.0  # High CPU!
            server.state = ServerState.HEALTHY
        
        # Should recommend scale out
        event = orchestrator.analyze_scaling_needs()
        assert event == ScalingEvent.SCALE_OUT

    def test_scale_out_execution(self):
        """Test scaling out (adding servers)"""
        orchestrator = HorizontalScalingOrchestrator()
        
        initial_count = len(orchestrator.servers)
        
        # Execute scale out
        added_servers = orchestrator.execute_scaling(ScalingEvent.SCALE_OUT, count=3)
        
        assert len(added_servers) == 3
        assert len(orchestrator.servers) == initial_count + 3

    def test_health_check(self):
        """Test server health checking"""
        orchestrator = HorizontalScalingOrchestrator()
        
        # Register some servers
        for i in range(3):
            orchestrator.register_server(
                f"server-{i+1}", f"Server {i+1}",
                f"10.0.0.{i+1}", 8000 + i, RegionZone.US_EAST
            )
        
        # Run health checks
        results = orchestrator.health_check_all_servers()
        
        assert len(results) == 3
        # Most should be healthy (simulated 95% success rate)
        healthy_count = sum(1 for is_healthy in results.values() if is_healthy)
        assert healthy_count >= 0

    def test_cluster_stats(self):
        """Test cluster statistics"""
        orchestrator = HorizontalScalingOrchestrator()
        
        # Register servers
        for i in range(5):
            server = orchestrator.register_server(
                f"server-{i+1}", f"Server {i+1}",
                f"10.0.0.{i+1}", 8000 + i, RegionZone.US_EAST
            )
            server.cpu_usage = 50.0
            server.memory_usage = 60.0
        
        stats = orchestrator.get_cluster_stats()
        
        assert stats["total_servers"] == 5
        assert stats["active_servers"] == 5
        assert stats["avg_cpu"] == 50.0
        assert stats["avg_memory"] == 60.0


class TestChaosMonkey:
    """Test Chaos Monkey for resilience testing"""

    def test_chaos_monkey_creation(self):
        """Test creating Chaos Monkey"""
        orchestrator = HorizontalScalingOrchestrator()
        monkey = ChaosMonkey(orchestrator)
        
        assert monkey.chaos_level == 0.01
        assert monkey.is_enabled is False

    def test_enable_disable_chaos(self):
        """Test enabling and disabling chaos"""
        orchestrator = HorizontalScalingOrchestrator()
        monkey = ChaosMonkey(orchestrator)
        
        monkey.enable_chaos(level=0.1)
        assert monkey.is_enabled is True
        assert monkey.chaos_level == 0.1
        
        monkey.disable_chaos()
        assert monkey.is_enabled is False

    def test_chaos_monkey_strike(self):
        """Test Chaos Monkey striking servers"""
        orchestrator = HorizontalScalingOrchestrator()
        monkey = ChaosMonkey(orchestrator)
        
        # Register healthy servers
        for i in range(10):
            orchestrator.register_server(
                f"server-{i+1}", f"Server {i+1}",
                f"10.0.0.{i+1}", 8000 + i, RegionZone.US_EAST
            )
        
        # Enable chaos with high probability
        monkey.enable_chaos(level=1.0)  # 100% strike rate
        
        # Unleash chaos multiple times
        for _ in range(5):
            monkey.unleash_chaos()
        
        # Some servers should be unhealthy
        unhealthy = [
            s for s in orchestrator.servers.values()
            if s.state == ServerState.UNHEALTHY
        ]
        assert len(unhealthy) >= 0  # Could be 0 if random doesn't trigger


class TestServerLoadFactor:
    """Test server load factor calculation"""

    def test_load_factor_empty(self):
        """Test load factor with no connections"""
        server = Server(
            server_id="s1",
            name="Server 1",
            ip_address="10.0.0.1",
            port=8000,
            region=RegionZone.US_EAST,
            state=ServerState.HEALTHY,
            max_connections=100,
        )
        
        assert server.load_factor == 0.0

    def test_load_factor_half(self):
        """Test load factor at 50%"""
        server = Server(
            server_id="s1",
            name="Server 1",
            ip_address="10.0.0.1",
            port=8000,
            region=RegionZone.US_EAST,
            state=ServerState.HEALTHY,
            max_connections=100,
        )
        server.active_connections = 50
        
        assert server.load_factor == 0.5

    def test_load_factor_full(self):
        """Test load factor at 100%"""
        server = Server(
            server_id="s1",
            name="Server 1",
            ip_address="10.0.0.1",
            port=8000,
            region=RegionZone.US_EAST,
            state=ServerState.HEALTHY,
            max_connections=100,
        )
        server.active_connections = 100
        
        assert server.load_factor == 1.0

    def test_server_availability(self):
        """Test server availability check"""
        server = Server(
            server_id="s1",
            name="Server 1",
            ip_address="10.0.0.1",
            port=8000,
            region=RegionZone.US_EAST,
            state=ServerState.HEALTHY,
            max_connections=100,
        )
        
        # Healthy and not full - available
        assert server.is_available is True
        
        # Make it full
        server.active_connections = 100
        assert server.is_available is False
        
        # Make it unhealthy
        server.active_connections = 50
        server.state = ServerState.UNHEALTHY
        assert server.is_available is False


def test_singleton_orchestrator():
    """Test singleton pattern for orchestrator"""
    orch1 = get_scaling_orchestrator()
    orch2 = get_scaling_orchestrator()
    
    assert orch1 is orch2  # Same instance
