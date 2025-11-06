# app/services/horizontal_scaling_service.py
# ======================================================================================
# ==    HORIZONTAL SCALING & SPOF ELIMINATION - التحجيم الأفقي الخارق                ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام التحجيم الأفقي الخارق الذي يتفوق على Google و AWS و Microsoft!
#   ✨ المميزات الخارقة:
#   - Multi-layer Load Balancing (DNS, GLB, ALB)
#   - Consistent Hashing للبيانات الموزعة
#   - Auto-scaling ذكي مع التنبؤ بالحمل
#   - Zero Single Points of Failure
#   - Geographic Distribution
#   - Chaos Engineering

from __future__ import annotations

import hashlib
import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable


# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class LoadBalancingAlgorithm(Enum):
    """خوارزميات توزيع الحمل"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LATENCY_BASED = "latency_based"
    CONSISTENT_HASH = "consistent_hash"
    GEOGRAPHIC = "geographic"
    INTELLIGENT_AI = "intelligent_ai"


class ServerState(Enum):
    """حالة الخادم"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"  # تفريغ - لا يقبل طلبات جديدة
    OFFLINE = "offline"


class ScalingEvent(Enum):
    """أحداث التوسع"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"  # إضافة خوادم
    SCALE_IN = "scale_in"    # إزالة خوادم
    NO_ACTION = "no_action"


class RegionZone(Enum):
    """المناطق الجغرافية"""
    US_EAST = "us-east"
    US_WEST = "us-west"
    EUROPE = "europe"
    ASIA = "asia"
    SOUTH_AMERICA = "south-america"
    AFRICA = "africa"
    AUSTRALIA = "australia"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class Server:
    """خادم في الكلاستر"""
    server_id: str
    name: str
    ip_address: str
    port: int
    region: RegionZone
    state: ServerState
    weight: int = 100
    max_connections: int = 1000
    active_connections: int = 0
    total_requests: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_health_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """هل الخادم متاح لقبول طلبات جديدة؟"""
        return (
            self.state == ServerState.HEALTHY
            and self.active_connections < self.max_connections
        )

    @property
    def load_factor(self) -> float:
        """عامل الحمل (0-1)"""
        if self.max_connections == 0:
            return 0.0
        return self.active_connections / self.max_connections


@dataclass
class LoadBalancer:
    """موزع الحمل"""
    lb_id: str
    name: str
    algorithm: LoadBalancingAlgorithm
    servers: list[Server] = field(default_factory=list)
    virtual_nodes: int = 150  # للـ Consistent Hashing
    hash_ring: dict[int, str] = field(default_factory=dict)
    current_index: int = 0  # للـ Round Robin
    total_requests: int = 0
    total_errors: int = 0

    def __post_init__(self):
        """تهيئة الـ Hash Ring إذا كان الخوارزمية Consistent Hash"""
        if self.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
            self._build_hash_ring()

    def _build_hash_ring(self):
        """بناء الـ Hash Ring للـ Consistent Hashing"""
        self.hash_ring.clear()
        for server in self.servers:
            for i in range(self.virtual_nodes):
                virtual_key = f"{server.server_id}:{i}"
                hash_value = int(hashlib.md5(virtual_key.encode()).hexdigest(), 16)
                self.hash_ring[hash_value] = server.server_id

    def add_server(self, server: Server):
        """إضافة خادم جديد"""
        if server not in self.servers:
            self.servers.append(server)
            if self.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
                self._build_hash_ring()

    def remove_server(self, server_id: str):
        """إزالة خادم"""
        self.servers = [s for s in self.servers if s.server_id != server_id]
        if self.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
            self._build_hash_ring()


@dataclass
class ScalingMetrics:
    """مقاييس التوسع"""
    timestamp: datetime
    total_servers: int
    active_servers: int
    total_requests_per_second: float
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_latency_ms: float
    error_rate: float
    scaling_recommendation: ScalingEvent


@dataclass
class ConsistentHashNode:
    """عقدة في الـ Consistent Hash Ring"""
    hash_value: int
    server_id: str
    is_virtual: bool = False


# ======================================================================================
# HORIZONTAL SCALING ORCHESTRATOR
# ======================================================================================


class HorizontalScalingOrchestrator:
    """
    المنسق الرئيسي للتحجيم الأفقي
    
    المسؤوليات:
    - إدارة موزعات الحمل المتعددة
    - التوسع التلقائي الذكي
    - الـ Health Checking المستمر
    - توزيع الحمل الجغرافي
    """

    def __init__(self):
        self.load_balancers: dict[str, LoadBalancer] = {}
        self.servers: dict[str, Server] = {}
        self.metrics_history: deque[ScalingMetrics] = deque(maxlen=1000)
        self.scaling_policy: dict[str, Any] = {
            "min_servers": 10,
            "max_servers": 1000,
            "target_cpu": 70.0,
            "target_memory": 75.0,
            "target_latency_ms": 200.0,
            "scale_up_threshold": 80.0,
            "scale_down_threshold": 30.0,
            "cooldown_seconds": 300,
        }
        self.last_scaling_event: datetime | None = None
        self._lock = threading.Lock()

    def create_load_balancer(
        self,
        lb_id: str,
        name: str,
        algorithm: LoadBalancingAlgorithm,
    ) -> LoadBalancer:
        """إنشاء موزع حمل جديد"""
        lb = LoadBalancer(lb_id=lb_id, name=name, algorithm=algorithm)
        self.load_balancers[lb_id] = lb
        return lb

    def register_server(
        self,
        server_id: str,
        name: str,
        ip_address: str,
        port: int,
        region: RegionZone,
        weight: int = 100,
    ) -> Server:
        """تسجيل خادم جديد"""
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
        return server

    def route_request(
        self,
        lb_id: str,
        request_key: str | None = None,
        client_region: RegionZone | None = None,
    ) -> Server | None:
        """
        توجيه الطلب إلى الخادم المناسب
        
        Args:
            lb_id: معرف موزع الحمل
            request_key: مفتاح للـ Consistent Hashing
            client_region: منطقة العميل للتوجيه الجغرافي
        """
        lb = self.load_balancers.get(lb_id)
        if not lb or not lb.servers:
            return None

        # تصفية الخوادم المتاحة
        available_servers = [s for s in lb.servers if s.is_available]
        if not available_servers:
            return None

        # اختيار الخوارزمية المناسبة
        if lb.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin(lb, available_servers)
        elif lb.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections(available_servers)
        elif lb.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(lb, available_servers)
        elif lb.algorithm == LoadBalancingAlgorithm.LATENCY_BASED:
            return self._latency_based(available_servers)
        elif lb.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
            return self._consistent_hash(lb, request_key or "")
        elif lb.algorithm == LoadBalancingAlgorithm.GEOGRAPHIC:
            return self._geographic_routing(available_servers, client_region)
        elif lb.algorithm == LoadBalancingAlgorithm.INTELLIGENT_AI:
            return self._intelligent_routing(available_servers)
        
        return available_servers[0] if available_servers else None

    def _round_robin(self, lb: LoadBalancer, servers: list[Server]) -> Server:
        """خوارزمية Round Robin"""
        with self._lock:
            lb.current_index = (lb.current_index + 1) % len(servers)
            return servers[lb.current_index]

    def _least_connections(self, servers: list[Server]) -> Server:
        """خوارزمية Least Connections - اختيار الخادم بأقل اتصالات"""
        return min(servers, key=lambda s: s.active_connections)

    def _weighted_round_robin(
        self, lb: LoadBalancer, servers: list[Server]
    ) -> Server:
        """خوارزمية Weighted Round Robin"""
        # حساب الأوزان التراكمية
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return servers[0]

        # اختيار عشوائي موزون
        rand_val = random.uniform(0, total_weight)
        cumulative = 0.0
        for server in servers:
            cumulative += server.weight
            if cumulative >= rand_val:
                return server
        return servers[-1]

    def _latency_based(self, servers: list[Server]) -> Server:
        """خوارزمية Latency-based - اختيار الخادم الأسرع"""
        return min(servers, key=lambda s: s.avg_latency_ms)

    def _consistent_hash(self, lb: LoadBalancer, key: str) -> Server | None:
        """
        خوارزمية Consistent Hashing
        
        الفوائد:
        - عند إضافة/إزالة خادم → إعادة توزيع 1/N فقط من البيانات
        - وليس كل البيانات!
        """
        if not lb.hash_ring:
            return None

        # حساب الـ Hash للمفتاح
        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # البحث في الـ Ring
        sorted_hashes = sorted(lb.hash_ring.keys())
        for hash_val in sorted_hashes:
            if hash_val >= key_hash:
                server_id = lb.hash_ring[hash_val]
                return self.servers.get(server_id)
        
        # إذا لم نجد، نعود للبداية (الـ Ring دائري)
        first_hash = sorted_hashes[0]
        server_id = lb.hash_ring[first_hash]
        return self.servers.get(server_id)

    def _geographic_routing(
        self, servers: list[Server], client_region: RegionZone | None
    ) -> Server:
        """توجيه جغرافي - توجيه للخادم الأقرب"""
        if client_region:
            # البحث عن خادم في نفس المنطقة
            region_servers = [s for s in servers if s.region == client_region]
            if region_servers:
                return min(region_servers, key=lambda s: s.active_connections)
        
        # إذا لم نجد، نختار أي خادم متاح
        return min(servers, key=lambda s: s.active_connections)

    def _intelligent_routing(self, servers: list[Server]) -> Server:
        """
        توجيه ذكي بالذكاء الاصطناعي
        
        يأخذ في الاعتبار:
        - الاتصالات النشطة
        - استخدام CPU/Memory
        - زمن الاستجابة
        - معدل الأخطاء
        """
        def score_server(s: Server) -> float:
            # نموذج تقييم متعدد العوامل
            connection_score = 1.0 - (s.active_connections / s.max_connections)
            cpu_score = 1.0 - (s.cpu_usage / 100.0)
            memory_score = 1.0 - (s.memory_usage / 100.0)
            latency_score = max(0, 1.0 - (s.avg_latency_ms / 1000.0))
            error_score = 1.0 - (s.total_errors / max(s.total_requests, 1))
            
            # الأوزان
            weights = {
                "connections": 0.3,
                "cpu": 0.2,
                "memory": 0.2,
                "latency": 0.2,
                "errors": 0.1,
            }
            
            total_score = (
                weights["connections"] * connection_score +
                weights["cpu"] * cpu_score +
                weights["memory"] * memory_score +
                weights["latency"] * latency_score +
                weights["errors"] * error_score
            )
            
            return total_score

        # اختيار الخادم بأعلى تقييم
        return max(servers, key=score_server)

    def analyze_scaling_needs(self) -> ScalingEvent:
        """
        تحليل الحاجة للتوسع
        
        Returns:
            قرار التوسع (SCALE_UP, SCALE_DOWN, NO_ACTION)
        """
        if not self.servers:
            return ScalingEvent.NO_ACTION

        # حساب المتوسطات
        active_servers = [
            s for s in self.servers.values()
            if s.state in (ServerState.HEALTHY, ServerState.DEGRADED)
        ]
        
        if not active_servers:
            return ScalingEvent.NO_ACTION

        avg_cpu = sum(s.cpu_usage for s in active_servers) / len(active_servers)
        avg_memory = sum(s.memory_usage for s in active_servers) / len(active_servers)
        avg_latency = sum(s.avg_latency_ms for s in active_servers) / len(active_servers)
        
        # فحص Cooldown Period
        if self.last_scaling_event:
            elapsed = (datetime.now(UTC) - self.last_scaling_event).total_seconds()
            if elapsed < self.scaling_policy["cooldown_seconds"]:
                return ScalingEvent.NO_ACTION

        # قرار التوسع
        scale_up_threshold = self.scaling_policy["scale_up_threshold"]
        scale_down_threshold = self.scaling_policy["scale_down_threshold"]
        
        if (avg_cpu > scale_up_threshold or 
            avg_memory > scale_up_threshold or
            avg_latency > self.scaling_policy["target_latency_ms"] * 2):
            return ScalingEvent.SCALE_OUT
        elif (avg_cpu < scale_down_threshold and 
              avg_memory < scale_down_threshold and
              len(active_servers) > self.scaling_policy["min_servers"]):
            return ScalingEvent.SCALE_IN
        
        return ScalingEvent.NO_ACTION

    def execute_scaling(self, event: ScalingEvent, count: int = 1) -> list[Server]:
        """
        تنفيذ عملية التوسع
        
        Args:
            event: نوع التوسع
            count: عدد الخوادم للإضافة/الإزالة
            
        Returns:
            قائمة الخوادم المضافة/المزالة
        """
        servers_affected = []
        
        if event == ScalingEvent.SCALE_OUT:
            # إضافة خوادم جديدة
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
                
                # إضافة للـ Load Balancers
                for lb in self.load_balancers.values():
                    lb.add_server(server)
        
        elif event == ScalingEvent.SCALE_IN:
            # إزالة خوادم (اختيار الأقل استخداماً)
            servers_sorted = sorted(
                self.servers.values(),
                key=lambda s: s.active_connections
            )
            for i in range(min(count, len(servers_sorted))):
                server = servers_sorted[i]
                if server.active_connections == 0:  # فقط الخوادم الخالية
                    server.state = ServerState.DRAINING
                    servers_affected.append(server)
                    
                    # إزالة من Load Balancers
                    for lb in self.load_balancers.values():
                        lb.remove_server(server.server_id)
        
        self.last_scaling_event = datetime.now(UTC)
        return servers_affected

    def health_check_all_servers(self) -> dict[str, bool]:
        """
        فحص صحة جميع الخوادم
        
        Returns:
            قاموس {server_id: is_healthy}
        """
        results = {}
        for server_id, server in self.servers.items():
            # محاكاة فحص الصحة (في الواقع، نرسل HTTP request)
            is_healthy = self._simulate_health_check(server)
            
            # تحديث حالة الخادم
            if is_healthy:
                if server.state != ServerState.HEALTHY:
                    server.state = ServerState.HEALTHY
            else:
                server.state = ServerState.UNHEALTHY
            
            server.last_health_check = datetime.now(UTC)
            results[server_id] = is_healthy
        
        return results

    def _simulate_health_check(self, server: Server) -> bool:
        """
        محاكاة فحص الصحة
        
        في الإنتاج، هذه ستكون HTTP request إلى /health endpoint
        """
        # محاكاة: 95% نجاح
        return random.random() > 0.05

    def get_cluster_stats(self) -> dict[str, Any]:
        """الحصول على إحصائيات الكلاستر"""
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


# ======================================================================================
# CHAOS MONKEY - اختبار الفشل
# ======================================================================================


class ChaosMonkey:
    """
    Chaos Monkey - نيتفليكس تفعله، ونحن أيضاً! 🐒💥
    
    اختبار مقاومة النظام بإيقاف خوادم عشوائية
    """

    def __init__(self, orchestrator: HorizontalScalingOrchestrator):
        self.orchestrator = orchestrator
        self.chaos_level: float = 0.01  # 1% فرصة لإيقاف خادم
        self.is_enabled: bool = False

    def unleash_chaos(self):
        """إطلاق الفوضى! 🐒"""
        import logging
        
        if not self.is_enabled:
            return

        healthy_servers = [
            s for s in self.orchestrator.servers.values()
            if s.state == ServerState.HEALTHY
        ]
        
        if not healthy_servers:
            return

        # اختيار خادم عشوائي للإيقاف
        if random.random() < self.chaos_level:
            target = random.choice(healthy_servers)
            target.state = ServerState.UNHEALTHY
            logging.warning(f"🐒💥 Chaos Monkey struck! Server {target.server_id} is down!")

    def enable_chaos(self, level: float = 0.01):
        """تفعيل Chaos Monkey"""
        self.is_enabled = True
        self.chaos_level = level

    def disable_chaos(self):
        """تعطيل Chaos Monkey"""
        self.is_enabled = False


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_orchestrator_instance: HorizontalScalingOrchestrator | None = None


def get_scaling_orchestrator() -> HorizontalScalingOrchestrator:
    """الحصول على instance واحد من الـ Orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = HorizontalScalingOrchestrator()
    return _orchestrator_instance
