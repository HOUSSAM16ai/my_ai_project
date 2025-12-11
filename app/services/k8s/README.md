# Kubernetes Orchestration Service - Hexagonal Architecture

## Overview

Refactored Kubernetes orchestration service from monolithic design to Hexagonal Architecture (Ports & Adapters).

**Original**: 715 lines / 27KB monolithic service  
**New**: 13 specialized files with clear separation of concerns

## Architecture

```
app/services/k8s/
│
├── __init__.py                    # Public API
├── facade.py                      # Backward compatible facade
├── README.md                      # This file
│
├── domain/                        # Domain Layer (3 files)
│   ├── __init__.py
│   ├── models.py                  # Entities & Value Objects
│   └── ports.py                   # Interfaces/Protocols
│
├── application/                   # Application Layer (5 files)
│   ├── __init__.py
│   ├── pod_scheduler.py           # Pod scheduling logic
│   ├── auto_scaler.py             # Auto-scaling logic
│   ├── self_healer.py             # Self-healing logic
│   ├── health_monitor.py          # Health monitoring
│   └── consensus_manager.py       # Raft consensus
│
└── infrastructure/                # Infrastructure Layer (2 files)
    ├── __init__.py
    ├── in_memory_pod_repository.py    # Pod storage
    └── in_memory_node_repository.py   # Node storage
```

## Components

### Domain Layer

**models.py** - Core entities:
- `Pod`: Kubernetes pod entity
- `Node`: Cluster node entity
- `RaftState`: Consensus protocol state
- `AutoScalingConfig`: Auto-scaling configuration
- `SelfHealingEvent`: Healing event record
- Enums: `PodPhase`, `NodeState`, `ConsensusRole`, `ScalingDirection`

**ports.py** - Interfaces:
- `PodRepositoryPort`: Pod storage operations
- `NodeRepositoryPort`: Node storage operations
- `SchedulerPort`: Pod scheduling
- `AutoScalerPort`: Auto-scaling operations
- `SelfHealingPort`: Self-healing operations
- `HealthMonitorPort`: Health monitoring
- `ConsensusPort`: Distributed consensus

### Application Layer

**pod_scheduler.py** - Pod Scheduling
- Find best node for pod based on resources
- Schedule pod on selected node
- Update pod and node states

**auto_scaler.py** - Auto-Scaling
- Monitor resource utilization
- Scale deployments up/down based on thresholds
- Respect cooldown periods

**self_healer.py** - Self-Healing
- Detect and heal failed pods
- Evacuate pods from unhealthy nodes
- Record healing events

**health_monitor.py** - Health Monitoring
- Continuous pod health checking
- Continuous node health checking
- Trigger healing on failures

**consensus_manager.py** - Raft Consensus
- Leader election
- Log replication
- Heartbeat management
- Distributed decision making

### Infrastructure Layer

**in_memory_pod_repository.py** - Pod Storage
- Thread-safe in-memory pod storage
- CRUD operations for pods

**in_memory_node_repository.py** - Node Storage
- Thread-safe in-memory node storage
- CRUD operations for nodes

## Usage

### Basic Usage (Backward Compatible)

```python
from app.services.k8s import (
    KubernetesOrchestrator,
    get_kubernetes_orchestrator,
    Pod,
    PodPhase,
    AutoScalingConfig,
)

# Get singleton instance
k8s = get_kubernetes_orchestrator()

# Schedule a pod
pod = Pod(
    pod_id="pod-123",
    name="my-app",
    namespace="default",
    node_id="",
    phase=PodPhase.PENDING,
    container_image="nginx:latest",
)
k8s.schedule_pod(pod)

# Configure auto-scaling
config = AutoScalingConfig(
    config_id="config-1",
    deployment_name="my-app",
    namespace="default",
    min_replicas=2,
    max_replicas=10,
)
k8s.configure_autoscaling(config)

# Get cluster stats
stats = k8s.get_cluster_stats()
print(f"Total nodes: {stats['total_nodes']}")
print(f"Running pods: {stats['running_pods']}")
```

### Advanced Usage (Direct Component Access)

```python
from app.services.k8s.application import PodScheduler, AutoScaler
from app.services.k8s.infrastructure import (
    InMemoryPodRepository,
    InMemoryNodeRepository,
)

# Create repositories
pod_repo = InMemoryPodRepository()
node_repo = InMemoryNodeRepository()

# Create scheduler
scheduler = PodScheduler(pod_repo, node_repo)

# Schedule pod
scheduler.schedule_pod(pod)

# Create auto-scaler
auto_scaler = AutoScaler(pod_repo, node_repo)
auto_scaler.configure_autoscaling(config)
auto_scaler.check_autoscaling()
```

## Features

### Self-Healing
- Automatic pod restart on failure
- Reschedule pods after multiple failures
- Node evacuation on node failure
- Event logging for all healing actions

### Distributed Consensus (Raft)
- Leader election
- Log replication
- Heartbeat mechanism
- Fault tolerance

### Auto-Scaling
- CPU-based scaling
- Memory-based scaling
- Configurable thresholds
- Cooldown periods

### Health Monitoring
- Continuous pod health checks
- Continuous node health checks
- Automatic failure detection
- Callback-based healing triggers

## Benefits

### Before (Monolithic)
- ❌ 715 lines in single file
- ❌ 8+ responsibilities mixed together
- ❌ Difficult to test
- ❌ Hard to maintain
- ❌ Tight coupling

### After (Hexagonal)
- ✅ 13 specialized files
- ✅ Single Responsibility Principle
- ✅ Easy to test each component
- ✅ Easy to maintain and extend
- ✅ Loose coupling via ports
- ✅ 100% backward compatible

## Testing

Run tests:
```bash
python test_k8s_refactoring.py
```

## Migration Guide

No migration needed! The facade maintains 100% backward compatibility with the original API.

### Old Code (Still Works)
```python
from app.services.kubernetes_orchestration_service import (
    get_kubernetes_orchestrator,
    Pod,
    PodPhase,
)

k8s = get_kubernetes_orchestrator()
k8s.schedule_pod(pod)
```

### New Code (Recommended)
```python
from app.services.k8s import (
    get_kubernetes_orchestrator,
    Pod,
    PodPhase,
)

k8s = get_kubernetes_orchestrator()
k8s.schedule_pod(pod)
```

## Future Enhancements

### Planned
- PostgreSQL repository implementation
- Redis-based distributed consensus
- Prometheus metrics integration
- Kubernetes API client adapter
- Advanced scheduling algorithms
- Resource quotas and limits

### Easy to Add
Thanks to Hexagonal Architecture, new features can be added by:
1. Creating new application services
2. Implementing new infrastructure adapters
3. No changes to domain layer
4. Backward compatibility maintained

## Principles Applied

- **Single Responsibility Principle**: Each class has one reason to change
- **Dependency Inversion**: Depend on abstractions (ports), not concretions
- **Hexagonal Architecture**: Domain at center, infrastructure at edges
- **Ports & Adapters**: Clear boundaries between layers
- **Open/Closed**: Open for extension, closed for modification

---

**Built with ❤️ by Houssam Benmerah**

*Applying Clean Architecture & SOLID Principles*
