# Kubernetes Orchestration Service Refactoring Plan - Wave 2

## Current State
- **File**: `app/services/kubernetes_orchestration_service.py`
- **Size**: 715 lines / 27KB
- **Responsibilities**: 6+ (Self-Healing, Consensus, Scheduling, Auto-Scaling, Monitoring, Load Balancing)

## Target Architecture

```
app/k8s/
├── __init__.py
├── facade.py                      # KubernetesOrchestrator (backward compatible)
├── README.md
│
├── domain/
│   ├── models.py                  # Pod, Node, RaftState, AutoScalingConfig
│   ├── enums.py                   # PodPhase, NodeState, ConsensusRole, ScalingDirection
│   └── ports.py                   # ClusterStorePort, ConsensusPort, SchedulerPort
│
├── application/
│   ├── self_healing.py            # Self-healing logic
│   ├── consensus_manager.py       # Raft consensus protocol
│   ├── pod_scheduler.py           # Pod scheduling
│   ├── autoscaler.py              # Auto-scaling logic
│   └── health_monitor.py          # Health monitoring
│
└── infrastructure/
    ├── in_memory_cluster_store.py # In-memory cluster state
    └── mock_consensus.py          # Mock consensus for testing
```

## Responsibilities Breakdown

### Domain Layer
- **Models**: Pod, Node, RaftState, AutoScalingConfig, SelfHealingEvent
- **Enums**: PodPhase, NodeState, ConsensusRole, ScalingDirection
- **Ports**: ClusterStorePort, ConsensusPort, SchedulerPort

### Application Layer
1. **SelfHealing**: _heal_failed_pod(), _evacuate_node()
2. **ConsensusManager**: Raft protocol, elections, log replication
3. **PodScheduler**: schedule_pod(), _find_best_node_for_pod()
4. **AutoScaler**: check_autoscaling(), _scale_deployment()
5. **HealthMonitor**: _check_pod_health(), _check_node_health()

### Infrastructure Layer
- **InMemoryClusterStore**: Stores pods, nodes, state
- **MockConsensus**: Simulates distributed consensus

## Migration Strategy
1. Create domain layer (models, enums, ports)
2. Create infrastructure layer
3. Create application layer (5 services)
4. Create facade with delegation
5. Add README.md

## Success Metrics
- Reduce from 715 lines to ~150 lines (facade)
- 11+ specialized files
- Single responsibility per file
- 100% backward compatible
