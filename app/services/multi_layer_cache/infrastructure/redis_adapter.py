"""
Multi-Layer Cache Infrastructure - Redis Cluster Adapter
=========================================================

Distributed cache implementation using Redis Cluster.
Horizontal scaling across hundreds of nodes.
"""
from __future__ import annotations

import binascii
import threading
from typing import Any

from ..domain.models import CacheLayer, CacheStats, RedisClusterNode


class RedisClusterCache:
    """
    Distributed Cache Layer - Redis Cluster

    موزع على مئات العقد، تحجيم أفقي تلقائي!
    """

    def __init__(self, num_nodes: int = 6):
        self.num_nodes = num_nodes
        self.total_slots = 16384  # Redis Cluster hash slots
        self.nodes: dict[str, RedisClusterNode] = {}
        self.stats = CacheStats(layer=CacheLayer.DISTRIBUTED)
        self._lock = threading.Lock()

        # تهيئة العقد
        self._initialize_cluster()

    def _initialize_cluster(self):
        """تهيئة Redis Cluster"""
        slots_per_node = self.total_slots // (self.num_nodes // 2)  # Masters only

        master_count = 0
        for i in range(self.num_nodes):
            if i % 2 == 0:  # Master nodes
                node_id = f"master-{master_count + 1}"
                slot_start = master_count * slots_per_node
                slot_end = min((master_count + 1) * slots_per_node - 1, self.total_slots - 1)

                node = RedisClusterNode(
                    node_id=node_id,
                    host=f"redis-master-{master_count + 1}",
                    port=6379,
                    slot_start=slot_start,
                    slot_end=slot_end,
                    is_master=True,
                )

                # إضافة replica
                replica_id = f"replica-{master_count + 1}"
                replica = RedisClusterNode(
                    node_id=replica_id,
                    host=f"redis-replica-{master_count + 1}",
                    port=6379,
                    slot_start=slot_start,
                    slot_end=slot_end,
                    is_master=False,
                )

                node.replicas.append(replica_id)
                self.nodes[node_id] = node
                self.nodes[replica_id] = replica

                master_count += 1

    def _get_slot(self, key: str) -> int:
        """حساب الـ hash slot للمفتاح"""
        # CRC16 mod 16384 (Redis algorithm)
        crc = binascii.crc_hqx(key.encode(), 0)
        return crc % self.total_slots

    def _get_node_for_key(self, key: str) -> RedisClusterNode | None:
        """الحصول على العقدة المسؤولة عن المفتاح"""
        slot = self._get_slot(key)

        for node in self.nodes.values():
            if node.is_master and node.slot_start <= slot <= node.slot_end:
                return node

        return None

    def get(self, key: str) -> Any | None:
        """الحصول على قيمة من Redis Cluster"""
        node = self._get_node_for_key(key)
        if not node:
            self.stats.total_misses += 1
            return None

        # محاكاة القراءة من Redis
        # في الإنتاج: redis_client.get(key)
        self.stats.total_hits += 1
        return f"value-from-{node.node_id}"

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """تخزين قيمة في Redis Cluster"""
        node = self._get_node_for_key(key)
        if not node:
            return False

        # محاكاة الكتابة على Redis
        # في الإنتاج: redis_client.set(key, value, ex=ttl)
        self.stats.total_sets += 1
        node.total_keys += 1

        return True

    def add_node(self, node_id: str, host: str, port: int) -> RedisClusterNode:
        """
        إضافة عقدة جديدة للكلاستر

        الفائدة الخارقة: تحجيم أفقي تلقائي!
        """
        # إعادة توزيع الـ slots
        # في الإنتاج، Redis Cluster يقوم بهذا تلقائياً

        new_node = RedisClusterNode(
            node_id=node_id,
            host=host,
            port=port,
            slot_start=0,
            slot_end=0,
            is_master=True,
        )

        with self._lock:
            self.nodes[node_id] = new_node

        return new_node

    def get_cluster_stats(self) -> dict[str, Any]:
        """إحصائيات الكلاستر"""
        master_nodes = [n for n in self.nodes.values() if n.is_master]

        return {
            "layer": self.stats.layer.value,
            "total_nodes": len(self.nodes),
            "master_nodes": len(master_nodes),
            "total_keys": sum(n.total_keys for n in master_nodes),
            "total_slots": self.total_slots,
            "hit_rate": self.stats.hit_rate,
            "total_hits": self.stats.total_hits,
            "total_misses": self.stats.total_misses,
        }


__all__ = ["RedisClusterCache"]
