from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class ResourceType(Enum):
    """Resource type enumeration"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"


class HealthStatus(Enum):
    """System health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DOWN = "down"


@dataclass
class CPUMetrics:
    """CPU utilization metrics"""

    usage_percent: float
    user_percent: float
    system_percent: float
    idle_percent: float
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    core_count: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MemoryMetrics:
    """Memory utilization metrics"""

    total_bytes: int
    available_bytes: int
    used_bytes: int
    used_percent: float
    swap_total_bytes: int
    swap_used_bytes: int
    swap_percent: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DiskMetrics:
    """Disk utilization metrics"""

    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float
    read_bytes_per_sec: float
    write_bytes_per_sec: float
    read_iops: float
    write_iops: float
    mount_point: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class NetworkMetrics:
    """Network utilization metrics"""

    bytes_sent_per_sec: float
    bytes_recv_per_sec: float
    packets_sent_per_sec: float
    packets_recv_per_sec: float
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int
    connections_active: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProcessMetrics:
    """Process-level metrics"""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_bytes: int
    threads: int
    open_files: int
    connections: int
    status: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SystemHealthSnapshot:
    """Complete system health snapshot"""

    timestamp: datetime
    status: HealthStatus
    cpu: CPUMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics
    uptime_seconds: float
    platform_info: dict[str, str]


@dataclass
class AvailabilityMetrics:
    """Service availability metrics"""

    service_name: str
    uptime_seconds: float
    downtime_seconds: float
    availability_percent: float
    incidents_count: int
    mtbf_seconds: float  # Mean Time Between Failures
    mttr_seconds: float  # Mean Time To Repair
    last_incident: datetime | None
    sla_target: float  # Target availability (e.g., 99.9%)
    sla_compliance: bool
