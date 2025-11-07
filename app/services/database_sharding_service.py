# app/services/database_sharding_service.py
# ======================================================================================
# ==    DATABASE SHARDING & MULTI-MASTER REPLICATION - تجزئة قواعد البيانات          ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام تجزئة قواعد البيانات الخارق مع Multi-Master Replication
#   ✨ المميزات الخارقة:
#   - Range-based Sharding
#   - Hash-based Sharding
#   - Geographic Sharding
#   - Multi-Master Replication
#   - Automatic Shard Rebalancing
#   - Cross-Shard Queries

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class ShardingStrategy(Enum):
    """استراتيجيات التجزئة"""

    RANGE_BASED = "range_based"  # حسب النطاق
    HASH_BASED = "hash_based"  # حسب الـ Hash
    GEOGRAPHIC = "geographic"  # حسب الموقع الجغرافي
    LIST_BASED = "list_based"  # حسب قائمة محددة
    COMPOSITE = "composite"  # مزيج من الاستراتيجيات


class ShardState(Enum):
    """حالة الشارد"""

    ACTIVE = "active"
    READONLY = "readonly"
    MIGRATING = "migrating"
    OFFLINE = "offline"


class ReplicationRole(Enum):
    """دور النسخة في التكرار"""

    MASTER = "master"  # يمكن الكتابة
    REPLICA = "replica"  # للقراءة فقط
    MULTI_MASTER = "multi_master"  # يمكن الكتابة في جميع النسخ


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class DatabaseShard:
    """شارد قاعدة بيانات"""

    shard_id: str
    name: str
    connection_string: str
    state: ShardState
    role: ReplicationRole

    # Range-based sharding
    range_start: int | None = None
    range_end: int | None = None

    # Geographic sharding
    region: str | None = None

    # List-based sharding
    partition_keys: list[str] = field(default_factory=list)

    # Metrics
    total_records: int = 0
    storage_size_mb: float = 0.0
    read_qps: float = 0.0  # Queries per second
    write_qps: float = 0.0
    avg_query_latency_ms: float = 0.0

    # Health
    is_healthy: bool = True
    last_health_check: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Replication
    replicas: list[str] = field(default_factory=list)  # IDs of replica shards
    replication_lag_ms: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ShardingConfig:
    """إعدادات التجزئة"""

    strategy: ShardingStrategy
    shard_key: str  # الحقل المستخدم للتجزئة (مثل user_id)
    num_shards: int = 3
    replicas_per_shard: int = 3

    # Range-based config
    range_intervals: list[tuple[int, int]] = field(default_factory=list)

    # Hash-based config
    hash_function: str = "md5"

    # Geographic config
    regions: list[str] = field(default_factory=list)

    # Rebalancing
    auto_rebalance: bool = True
    rebalance_threshold_mb: float = 100000  # 100GB difference triggers rebalance


@dataclass
class ShardQuery:
    """استعلام على الشاردات"""

    query_id: str
    query_text: str
    shard_key_value: Any
    target_shards: list[str] = field(default_factory=list)
    is_cross_shard: bool = False
    estimated_cost: float = 1.0


# ======================================================================================
# DATABASE SHARDING MANAGER
# ======================================================================================


class DatabaseShardingManager:
    """
    مدير تجزئة قواعد البيانات

    المسؤوليات:
    - إدارة الشاردات المتعددة
    - توجيه الاستعلامات للشارد المناسب
    - التوازن التلقائي للبيانات
    - Multi-Master Replication
    """

    def __init__(self, config: ShardingConfig):
        self.config = config
        self.shards: dict[str, DatabaseShard] = {}
        self.routing_table: dict[Any, str] = {}  # {key_value: shard_id}
        self._lock = threading.Lock()

        # Initialize shards
        self._initialize_shards()

    def _initialize_shards(self):
        """تهيئة الشاردات الأولية"""
        if self.config.strategy == ShardingStrategy.RANGE_BASED:
            self._init_range_shards()
        elif self.config.strategy == ShardingStrategy.HASH_BASED:
            self._init_hash_shards()
        elif self.config.strategy == ShardingStrategy.GEOGRAPHIC:
            self._init_geographic_shards()

    def _init_range_shards(self):
        """تهيئة Range-based Shards"""
        # مثال: Users 1-1M → Shard A, 1M-2M → Shard B
        ranges = [
            (1, 1000000),
            (1000001, 2000000),
            (2000001, 3000000),
        ]

        for i, (start, end) in enumerate(ranges):
            shard_id = f"shard-range-{i+1}"
            shard = DatabaseShard(
                shard_id=shard_id,
                name=f"Range Shard {start}-{end}",
                connection_string=f"postgresql://db-{i+1}:5432/shard_{i+1}",
                state=ShardState.ACTIVE,
                role=ReplicationRole.MASTER,
                range_start=start,
                range_end=end,
            )

            # إنشاء النسخ المتماثلة
            replica_ids = []
            for r in range(self.config.replicas_per_shard):
                replica_id = f"{shard_id}-replica-{r+1}"
                replica = DatabaseShard(
                    shard_id=replica_id,
                    name=f"Replica {r+1} of {shard.name}",
                    connection_string=f"postgresql://db-{i+1}-replica-{r+1}:5432/shard_{i+1}",
                    state=ShardState.ACTIVE,
                    role=ReplicationRole.REPLICA,
                    range_start=start,
                    range_end=end,
                )
                self.shards[replica_id] = replica
                replica_ids.append(replica_id)

            shard.replicas = replica_ids
            self.shards[shard_id] = shard

    def _init_hash_shards(self):
        """تهيئة Hash-based Shards"""
        for i in range(self.config.num_shards):
            shard_id = f"shard-hash-{i+1}"
            shard = DatabaseShard(
                shard_id=shard_id,
                name=f"Hash Shard {i+1}",
                connection_string=f"postgresql://db-hash-{i+1}:5432/shard_{i+1}",
                state=ShardState.ACTIVE,
                role=ReplicationRole.MASTER,
            )

            # إنشاء النسخ
            replica_ids = []
            for r in range(self.config.replicas_per_shard):
                replica_id = f"{shard_id}-replica-{r+1}"
                replica = DatabaseShard(
                    shard_id=replica_id,
                    name=f"Replica {r+1} of {shard.name}",
                    connection_string=f"postgresql://db-hash-{i+1}-r{r+1}:5432/shard_{i+1}",
                    state=ShardState.ACTIVE,
                    role=ReplicationRole.REPLICA,
                )
                self.shards[replica_id] = replica
                replica_ids.append(replica_id)

            shard.replicas = replica_ids
            self.shards[shard_id] = shard

    def _init_geographic_shards(self):
        """تهيئة Geographic Shards"""
        regions = self.config.regions or ["us-east", "us-west", "europe", "asia"]

        for region in regions:
            shard_id = f"shard-{region}"
            shard = DatabaseShard(
                shard_id=shard_id,
                name=f"{region.upper()} Shard",
                connection_string=f"postgresql://db-{region}:5432/{region}",
                state=ShardState.ACTIVE,
                role=ReplicationRole.MULTI_MASTER,  # Multi-master للمناطق
                region=region,
            )

            # نسخ متماثلة في نفس المنطقة
            replica_ids = []
            for r in range(self.config.replicas_per_shard):
                replica_id = f"{shard_id}-replica-{r+1}"
                replica = DatabaseShard(
                    shard_id=replica_id,
                    name=f"Replica {r+1} in {region}",
                    connection_string=f"postgresql://db-{region}-r{r+1}:5432/{region}",
                    state=ShardState.ACTIVE,
                    role=ReplicationRole.REPLICA,
                    region=region,
                )
                self.shards[replica_id] = replica
                replica_ids.append(replica_id)

            shard.replicas = replica_ids
            self.shards[shard_id] = shard

    def get_shard_for_key(self, key_value: Any) -> DatabaseShard | None:
        """
        الحصول على الشارد المناسب لقيمة المفتاح

        Args:
            key_value: قيمة المفتاح (مثل user_id)

        Returns:
            الشارد المناسب
        """
        if self.config.strategy == ShardingStrategy.RANGE_BASED:
            return self._get_range_shard(key_value)
        elif self.config.strategy == ShardingStrategy.HASH_BASED:
            return self._get_hash_shard(key_value)
        elif self.config.strategy == ShardingStrategy.GEOGRAPHIC:
            return self._get_geographic_shard(key_value)

        return None

    def _get_range_shard(self, key_value: int) -> DatabaseShard | None:
        """الحصول على Range-based Shard"""
        for shard in self.shards.values():
            if shard.role == ReplicationRole.MASTER and shard.range_start and shard.range_end:
                if shard.range_start <= key_value <= shard.range_end:
                    return shard
        return None

    def _get_hash_shard(self, key_value: Any) -> DatabaseShard | None:
        """
        الحصول على Hash-based Shard

        الفائدة: توزيع متساوٍ تلقائياً
        """
        # حساب الـ Hash
        key_str = str(key_value)
        if self.config.hash_function == "md5":
            hash_val = int(hashlib.md5(key_str.encode()).hexdigest(), 16)
        else:
            hash_val = hash(key_str)

        # اختيار الشارد
        shard_index = hash_val % self.config.num_shards
        shard_id = f"shard-hash-{shard_index + 1}"

        return self.shards.get(shard_id)

    def _get_geographic_shard(self, region: str) -> DatabaseShard | None:
        """الحصول على Geographic Shard"""
        shard_id = f"shard-{region}"
        return self.shards.get(shard_id)

    def execute_query(
        self,
        query: ShardQuery,
        operation: str = "read",
    ) -> dict[str, Any]:
        """
        تنفيذ استعلام

        Args:
            query: الاستعلام
            operation: نوع العملية (read/write)

        Returns:
            نتائج الاستعلام
        """
        # الحصول على الشارد المناسب
        target_shard = self.get_shard_for_key(query.shard_key_value)

        if not target_shard:
            return {"success": False, "error": "No shard found for key"}

        # اختيار النسخة المناسبة
        if operation == "write":
            # الكتابة على الـ Master
            selected_shard = target_shard
        else:
            # القراءة من أي Replica
            if target_shard.replicas:
                # اختيار replica عشوائية لتوزيع الحمل
                import random

                replica_id = random.choice(target_shard.replicas)
                selected_shard = self.shards.get(replica_id, target_shard)
            else:
                selected_shard = target_shard

        # تنفيذ الاستعلام (محاكاة)
        result = {
            "success": True,
            "shard_id": selected_shard.shard_id,
            "query_id": query.query_id,
            "operation": operation,
            "latency_ms": selected_shard.avg_query_latency_ms,
        }

        # تحديث الإحصائيات
        if operation == "read":
            selected_shard.read_qps += 1
        else:
            selected_shard.write_qps += 1

        return result

    def execute_cross_shard_query(self, query: ShardQuery) -> dict[str, Any]:
        """
        تنفيذ استعلام عبر شاردات متعددة

        مثال: SELECT * FROM users WHERE age > 25
        (يحتاج قراءة من جميع الشاردات)
        """
        results: list[dict[str, Any]] = []
        master_shards = [
            s
            for s in self.shards.values()
            if s.role in (ReplicationRole.MASTER, ReplicationRole.MULTI_MASTER)
        ]

        for shard in master_shards:
            # تنفيذ على كل شارد
            shard_result: dict[str, Any] = {
                "shard_id": shard.shard_id,
                "query_id": query.query_id,
                "latency_ms": shard.avg_query_latency_ms,
            }
            results.append(shard_result)

        return {
            "success": True,
            "is_cross_shard": True,
            "shards_queried": len(results),
            "results": results,
            "total_latency_ms": max((float(r["latency_ms"]) for r in results), default=0.0),
        }

    def add_shard(
        self,
        shard_id: str,
        name: str,
        connection_string: str,
        **kwargs,
    ) -> DatabaseShard:
        """إضافة شارد جديد"""
        shard = DatabaseShard(
            shard_id=shard_id,
            name=name,
            connection_string=connection_string,
            state=ShardState.ACTIVE,
            role=kwargs.get("role", ReplicationRole.MASTER),
            range_start=kwargs.get("range_start"),
            range_end=kwargs.get("range_end"),
            region=kwargs.get("region"),
        )

        with self._lock:
            self.shards[shard_id] = shard

        return shard

    def rebalance_shards(self) -> dict[str, Any]:
        """
        إعادة توازن الشاردات

        ينقل البيانات من الشاردات الكبيرة إلى الصغيرة
        """
        master_shards = [
            s
            for s in self.shards.values()
            if s.role in (ReplicationRole.MASTER, ReplicationRole.MULTI_MASTER)
        ]

        if len(master_shards) < 2:
            return {"success": False, "reason": "Need at least 2 shards"}

        # حساب الحجم المتوسط
        avg_size = sum(s.storage_size_mb for s in master_shards) / len(master_shards)

        # إيجاد الشاردات غير المتوازنة
        oversized = [s for s in master_shards if s.storage_size_mb > avg_size * 1.5]
        undersized = [s for s in master_shards if s.storage_size_mb < avg_size * 0.5]

        if not oversized or not undersized:
            return {"success": True, "message": "Shards are balanced"}

        # خطة النقل (محاكاة)
        migration_plan = []
        for over_shard in oversized:
            for under_shard in undersized:
                # حساب البيانات للنقل
                to_migrate_mb = (over_shard.storage_size_mb - avg_size) / 2
                migration_plan.append(
                    {
                        "from_shard": over_shard.shard_id,
                        "to_shard": under_shard.shard_id,
                        "size_mb": to_migrate_mb,
                        "estimated_time_minutes": to_migrate_mb / 100,  # 100MB/min
                    }
                )

        return {
            "success": True,
            "migrations": len(migration_plan),
            "plan": migration_plan,
            "avg_size_mb": avg_size,
        }

    def get_shard_stats(self) -> dict[str, Any]:
        """الحصول على إحصائيات الشاردات"""
        master_shards = [
            s
            for s in self.shards.values()
            if s.role in (ReplicationRole.MASTER, ReplicationRole.MULTI_MASTER)
        ]

        total_replicas = sum(len(s.replicas) for s in master_shards)

        return {
            "total_shards": len(master_shards),
            "total_replicas": total_replicas,
            "strategy": self.config.strategy.value,
            "total_storage_mb": sum(s.storage_size_mb for s in master_shards),
            "total_records": sum(s.total_records for s in master_shards),
            "avg_read_qps": (
                sum(s.read_qps for s in master_shards) / len(master_shards) if master_shards else 0
            ),
            "avg_write_qps": (
                sum(s.write_qps for s in master_shards) / len(master_shards) if master_shards else 0
            ),
            "healthy_shards": sum(1 for s in master_shards if s.is_healthy),
        }


# ======================================================================================
# CONNECTION POOLING MANAGER
# ======================================================================================


@dataclass
class ConnectionPool:
    """مجموعة اتصالات قاعدة البيانات"""

    pool_id: str
    shard_id: str
    min_connections: int = 10
    max_connections: int = 100
    active_connections: int = 0
    idle_connections: int = 10
    total_connections: int = 10
    connection_timeout_ms: int = 30000
    idle_timeout_ms: int = 600000  # 10 minutes

    def acquire_connection(self) -> bool:
        """الحصول على اتصال من المجموعة"""
        if self.active_connections < self.max_connections:
            if self.idle_connections > 0:
                self.idle_connections -= 1
                self.active_connections += 1
                return True
            elif self.total_connections < self.max_connections:
                # إنشاء اتصال جديد
                self.total_connections += 1
                self.active_connections += 1
                return True
        return False

    def release_connection(self):
        """إرجاع اتصال للمجموعة"""
        if self.active_connections > 0:
            self.active_connections -= 1
            self.idle_connections += 1


class ConnectionPoolManager:
    """
    مدير مجموعات الاتصالات

    الفوائد:
    - إعادة استخدام الاتصالات → أسرع!
    - تقليل الحمل على قاعدة البيانات
    - التحكم في عدد الاتصالات
    """

    def __init__(self):
        self.pools: dict[str, ConnectionPool] = {}
        self._lock = threading.Lock()

    def create_pool(
        self,
        pool_id: str,
        shard_id: str,
        min_connections: int = 10,
        max_connections: int = 100,
    ) -> ConnectionPool:
        """إنشاء مجموعة اتصالات جديدة"""
        pool = ConnectionPool(
            pool_id=pool_id,
            shard_id=shard_id,
            min_connections=min_connections,
            max_connections=max_connections,
        )

        with self._lock:
            self.pools[pool_id] = pool

        return pool

    def get_connection(self, shard_id: str) -> tuple[bool, str]:
        """
        الحصول على اتصال

        Returns:
            (success, message)
        """
        pool = self.pools.get(shard_id)
        if not pool:
            return False, f"No pool for shard {shard_id}"

        if pool.acquire_connection():
            return True, "Connection acquired"
        else:
            return False, "No available connections"

    def release_connection(self, shard_id: str):
        """إرجاع اتصال"""
        pool = self.pools.get(shard_id)
        if pool:
            pool.release_connection()

    def get_pool_stats(self) -> dict[str, Any]:
        """إحصائيات المجموعات"""
        return {
            "total_pools": len(self.pools),
            "total_connections": sum(p.total_connections for p in self.pools.values()),
            "active_connections": sum(p.active_connections for p in self.pools.values()),
            "idle_connections": sum(p.idle_connections for p in self.pools.values()),
        }


# ======================================================================================
# SINGLETON INSTANCES
# ======================================================================================

_sharding_manager_instance: DatabaseShardingManager | None = None
_pool_manager_instance: ConnectionPoolManager | None = None


def get_sharding_manager(config: ShardingConfig | None = None) -> DatabaseShardingManager:
    """الحصول على instance واحد من مدير التجزئة"""
    global _sharding_manager_instance
    if _sharding_manager_instance is None:
        if config is None:
            # إعدادات افتراضية
            config = ShardingConfig(
                strategy=ShardingStrategy.HASH_BASED,
                shard_key="user_id",
                num_shards=3,
                replicas_per_shard=3,
            )
        _sharding_manager_instance = DatabaseShardingManager(config)
    return _sharding_manager_instance


def get_connection_pool_manager() -> ConnectionPoolManager:
    """الحصول على instance واحد من مدير مجموعات الاتصالات"""
    global _pool_manager_instance
    if _pool_manager_instance is None:
        _pool_manager_instance = ConnectionPoolManager()
    return _pool_manager_instance
