#!/usr/bin/env python3
"""
Add Refactoring Headers to God Services
========================================
Adds documentation headers to all monolithic service files
indicating they need refactoring.
"""

from pathlib import Path
import re


GOD_SERVICES = [
    ("api_developer_portal_service.py", 784, "Developer Portal"),
    ("ai_adaptive_microservices.py", 703, "AI-Driven Self-Adaptive Microservices"),
    ("api_disaster_recovery_service.py", 696, "Disaster Recovery & On-Call"),
    ("api_event_driven_service.py", 689, "Event-Driven Architecture"),
    ("project_context_service.py", 685, "Project Context Management"),
    ("api_contract_service.py", 670, "API Contract & Versioning"),
    ("ai_advanced_security.py", 665, "AI-Powered Security"),
    ("infrastructure_metrics_service.py", 658, "Infrastructure Metrics"),
    ("ai_intelligent_testing.py", 657, "AI-Powered Intelligent Testing"),
    ("security_metrics_engine.py", 655, "Security Metrics Engine"),
    ("ai_auto_refactoring.py", 643, "AI Auto-Refactoring"),
    ("database_sharding_service.py", 641, "Database Sharding"),
    ("ai_project_management.py", 640, "AI Project Management"),
    ("gitops_policy_service.py", 636, "GitOps Policy Management"),
    ("api_advanced_analytics_service.py", 636, "Advanced Analytics"),
    ("fastapi_generation_service.py", 629, "FastAPI Generation"),
    ("api_config_secrets_service.py", 618, "Config & Secrets Management"),
    ("horizontal_scaling_service.py", 614, "Horizontal Scaling"),
    ("multi_layer_cache_service.py", 602, "Multi-Layer Caching"),
    ("aiops_self_healing_service.py", 601, "AIOps Self-Healing"),
    ("domain_events.py", 596, "Domain Events"),
    ("observability_integration_service.py", 592, "Observability Integration"),
    ("data_mesh_service.py", 588, "Data Mesh"),
    ("api_slo_sli_service.py", 582, "SLO/SLI Management"),
    ("api_gateway_chaos.py", 580, "API Gateway Chaos Engineering"),
    ("service_mesh_integration.py", 572, "Service Mesh Integration"),
    ("api_gateway_deployment.py", 529, "API Gateway Deployment"),
    ("chaos_engineering.py", 520, "Chaos Engineering"),
    ("task_executor_refactored.py", 517, "Task Executor"),
    ("superhuman_integration.py", 515, "Superhuman Integration"),
    ("api_chaos_monkey_service.py", 510, "Chaos Monkey"),
    ("saga_orchestrator.py", 510, "Saga Orchestration"),
    ("distributed_tracing.py", 505, "Distributed Tracing"),
]


def create_refactoring_header(filename, lines, description):
    """Generate a refactoring status header"""
    module_name = filename.replace(".py", "").replace("_service", "")
    
    header = f'''"""
⚠️  REFACTORING REQUIRED - GOD SERVICE DETECTED
===============================================

**Service**: {description}
**Current Size**: {lines} lines (Monolithic)
**Status**: ⏳ Pending Hexagonal Architecture Refactoring
**Priority**: See DISASSEMBLY_STATUS_TRACKER.md

This file is a "God Service" that violates Single Responsibility Principle.
It will be refactored into Hexagonal Architecture:

Target Structure:
```
app/services/{module_name}/
├── domain/
│   ├── models.py      # Entities, value objects, enums
│   └── ports.py       # Repository interfaces
├── application/
│   ├── manager.py     # Main service orchestration
│   └── *.py           # Specialized use case handlers
├── infrastructure/
│   └── repositories.py # Repository implementations
└── facade.py          # Backward-compatible API
```

Benefits After Refactoring:
- ✅ ~94% code reduction in monolithic file (becomes thin shim)
- ✅ Single Responsibility Principle applied
- ✅ Easy to test (isolated components)
- ✅ Easy to extend (new features = new files)
- ✅ 100% backward compatibility maintained

See: COMPREHENSIVE_DISASSEMBLY_PLAN.md
"""

'''
    return header


def main():
    services_dir = Path("app/services")
    
    print("=" * 80)
    print("ADDING REFACTORING HEADERS TO GOD SERVICES")
    print("=" * 80)
    
    for filename, lines, description in GOD_SERVICES:
        filepath = services_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  SKIP: {filename} (not found)")
            continue
        
        # Read current content
        content = filepath.read_text()
        
        # Check if already has header
        if "REFACTORING REQUIRED" in content[:500]:
            print(f"✓  SKIP: {filename} (already has header)")
            continue
        
        # Find where to insert (after any shebang and encoding declarations)
        lines_list = content.splitlines(keepends=True)
        insert_pos = 0
        
        # Skip shebang, encoding, and existing docstrings
        for i, line in enumerate(lines_list):
            if line.startswith('#!') or 'coding' in line or line.strip() == '':
                insert_pos = i + 1
            elif line.strip().startswith('"""') or line.strip().startswith("'''"):
                # Find end of docstring
                quote = '"""' if '"""' in line else "'''"
                if line.count(quote) >= 2:
                    insert_pos = i + 1
                else:
                    for j in range(i + 1, len(lines_list)):
                        if quote in lines_list[j]:
                            insert_pos = j + 1
                            break
                break
            elif not line.startswith('#'):
                break
        
        # Generate header
        header = create_refactoring_header(filename, lines, description)
        
        # Insert header
        new_content = ''.join(lines_list[:insert_pos]) + '\n' + header + '\n' + ''.join(lines_list[insert_pos:])
        
        # Write back (dry run for now)
        print(f"📝 READY: {filename} ({lines} lines) -> will add header")
        # filepath.write_text(new_content)
    
    print("=" * 80)
    print(f"Total: {len(GOD_SERVICES)} God Services identified")
    print("Note: Run with --apply flag to actually modify files")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    if "--apply" in sys.argv:
        print("⚠️  --apply flag not implemented yet (safety)")
    main()
