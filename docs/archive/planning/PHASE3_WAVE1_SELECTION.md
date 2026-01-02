# 📋 Phase 3 Wave 1: File Selection & Responsibility Analysis
# المرحلة الثالثة - الموجة الأولى: اختيار الملفات وتحليل المسؤوليات

## 🎯 Wave 1 Selection Criteria

Based on Phase 1 & 2 analysis, we select files that:
1. **High Hotspot Score**: Critical complexity (CC > 50)
2. **Layer Mixing**: Mix API + Business + Infrastructure
3. **Domain Mixing**: Cross multiple domains
4. **Foundation Files**: Core services used across system

## 📊 Selected Files for Wave 1

### Priority 1: Core Infrastructure Files

#### 1. `app/services/agent_tools/core.py` (325 lines)
**Current Issues:**
- **Mixed Responsibilities**:
  - Tool registry management (infrastructure)
  - Decorator logic (application)
  - Validation (cross-cutting)
  - Metrics collection (cross-cutting)
  - Policy enforcement (domain)
  
- **SRP Violations**:
  - `tool()` decorator: 137 lines - does registration + validation + execution + metrics
  - Mixes registry management with tool execution
  - Combines argument validation with type coercion
  - Intertwines metrics with core logic

- **Layer Violations**:
  - No clear separation between domain and infrastructure
  - Global state management mixed with business logic
  - Direct dependency on multiple concerns

**Target Decomposition:**
```
core.py (325 lines)
  ↓ Decompose into:
  
1. app/services/agent_tools/domain/ports/
   - tool_registry.py (Protocol for registry operations)
   - tool_validator.py (Protocol for validation)
   
2. app/services/agent_tools/application/
   - tool_decorator.py (Decorator logic only)
   - tool_executor.py (Execution orchestration)
   
3. app/services/agent_tools/infrastructure/
   - in_memory_registry.py (Concrete registry implementation)
   - argument_validator.py (Validation implementation)
   
4. app/services/agent_tools/observability/
   - tool_metrics.py (Metrics collection)
   - tool_tracing.py (Execution tracing)
```

**Expected Reduction:**
- Main orchestrator: ~50 lines
- Each component: < 80 lines
- Total complexity reduction: ~60%

---

#### 2. `app/services/agent_tools/fs_tools.py` (550 lines, CC: 57)
**Current Issues:**
- **Mixed Responsibilities**:
  - File I/O operations
  - Path validation and security
  - Error handling
  - Result formatting
  
- **SRP Violations**:
  - Functions mix I/O with validation
  - Security checks embedded in business logic
  - Direct file system access without abstraction

**Target Decomposition:**
```
fs_tools.py (550 lines)
  ↓ Decompose into:
  
1. app/services/agent_tools/domain/
   - file_operations.py (Domain interfaces for file ops)
   
2. app/services/agent_tools/application/
   - file_tool_service.py (Orchestrates file operations)
   
3. app/services/agent_tools/infrastructure/
   - file_system_adapter.py (Actual I/O operations)
   - path_validator.py (Security validation)
   
4. app/services/agent_tools/security/
   - path_sanitizer.py (Path traversal protection)
   - access_control.py (Permission checks)
```

**Expected Reduction:**
- Main service: ~100 lines
- Each component: < 100 lines
- Total complexity reduction: ~55%

---

### Priority 2: Business Logic Heavy Files

#### 3. `app/services/llm_client_service.py` (359 lines)
**Status**: ⚠️ **Partially Refactored**
- ✅ PayloadBuilder extracted
- ✅ ResponseNormalizer extracted
- ✅ CostManager extracted
- ✅ CircuitBreaker extracted
- ✅ RetryStrategy extracted
- ⏳ Main orchestration still needs cleanup

**Remaining Work:**
- Extract streaming logic
- Separate mock client creation
- Clean up singleton management
- Document migration pattern

**Target State:**
```
llm_client_service.py
  ↓ Final cleanup:
  
1. app/ai/application/
   - llm_client_facade.py (Main public API)
   - streaming_handler.py (Streaming logic)
   
2. app/ai/infrastructure/
   - client_factory.py (Client creation logic)
   - mock_client.py (Mock implementation)
```

---

#### 4. `app/overmind/planning/multi_pass_arch_planner.py`
**Current Issues** (from Phase 2):
- `_build_plan()`: 275 lines - massive God function
- Mixes configuration loading, task creation, and plan assembly

**Target Decomposition:**
```
multi_pass_arch_planner.py
  ↓ Decompose _build_plan():
  
1. app/overmind/planning/builders/
   - plan_configuration.py (Config loading)
   - discovery_task_builder.py (t01-t07)
   - index_task_builder.py (t08-t10)
   - section_task_builder.py (t11-t18)
   - audit_task_builder.py (t19-t22)
   - finalization_task_builder.py (t23-t24)
   
2. app/overmind/planning/
   - plan_orchestrator.py (Main ~50 lines)
```

**Expected Reduction:**
- 275 lines → 50 lines main + 6 builders (~40 lines each)
- CC: 44 → 5 per method

---

#### 5. `app/services/project_context_service.py` (CC: 115 from Phase 1)
**Current Issues:**
- Highest complexity in Phase 1 analysis
- Mixed file reading, parsing, and context building
- No clear separation of concerns

**Target Decomposition:**
```
project_context_service.py
  ↓ Decompose into:
  
1. app/services/context/domain/
   - context_builder.py (Domain logic)
   - file_reader.py (Reading interface)
   
2. app/services/context/application/
   - context_service.py (Main orchestrator)
   - file_selector.py (Selection logic)
   
3. app/services/context/infrastructure/
   - file_system_reader.py (Actual reading)
   - cache_manager.py (Caching layer)
```

---

## 🔬 Responsibility Matrix Template

For each file, we document:

| Responsibility | Current Location | Target Layer | Target Component | CC | LOC |
|---------------|------------------|--------------|------------------|-----|-----|
| Tool Registration | core.py/tool() | Infrastructure | in_memory_registry.py | 2 | 40 |
| Argument Validation | core.py/tool() | Infrastructure | argument_validator.py | 3 | 50 |
| Execution Orchestration | core.py/tool() | Application | tool_executor.py | 4 | 60 |
| Metrics Collection | core.py/tool() | Observability | tool_metrics.py | 2 | 35 |
| ... | ... | ... | ... | ... | ... |

## 📐 Architecture Principles

### Layer Structure
```
app/services/agent_tools/
├── domain/              # Pure business logic, no I/O
│   ├── ports/          # Interfaces (Protocols)
│   └── models.py       # Domain entities
├── application/         # Use cases, orchestration
│   └── *_service.py    # Application services
├── infrastructure/      # External adapters
│   ├── registry/       # Registry implementations
│   └── filesystem/     # File system adapters
└── observability/       # Cross-cutting concerns
    ├── metrics.py
    └── tracing.py
```

### Design Patterns to Apply

1. **Strategy Pattern**: For different validation strategies
2. **Repository Pattern**: For tool registry
3. **Decorator Pattern**: For metrics/tracing
4. **Factory Pattern**: For tool creation
5. **Builder Pattern**: For complex object construction
6. **Chain of Responsibility**: For validation pipeline

## 📊 Success Metrics

### Per-File Targets
- ✅ No function > 50 lines
- ✅ No function CC > 5
- ✅ Each class has single responsibility
- ✅ Layers properly separated
- ✅ All tests pass (golden master)
- ✅ 100% backward compatibility

### Overall Wave 1 Targets
- ✅ 5 files refactored
- ✅ ~2000 lines restructured
- ✅ Average CC reduction: 60%
- ✅ Test coverage maintained: 95%+
- ✅ Zero functional regressions
- ✅ Pattern documented for Wave 2

## 🗓️ Implementation Timeline

### Week 1: Core Tools Refactoring
- Day 1-2: agent_tools/core.py decomposition
- Day 3-4: agent_tools/fs_tools.py decomposition
- Day 5: Testing and validation

### Week 2: Service Layer Refactoring  
- Day 1-2: llm_client_service.py final cleanup
- Day 3-4: multi_pass_arch_planner.py decomposition
- Day 5: Testing and validation

### Week 3: Context Service + Documentation
- Day 1-2: project_context_service.py refactoring
- Day 3: Integration testing
- Day 4-5: Pattern documentation and Wave 2 planning

## 📝 Refactoring Checklist

For each file:
- [ ] Responsibility analysis completed
- [ ] Target design blueprint created
- [ ] Interfaces (Protocols) defined
- [ ] Extract responsibilities incrementally
- [ ] Wire dependencies properly
- [ ] Tests updated/created
- [ ] Golden master tests pass
- [ ] Metrics show improvement
- [ ] Documentation updated
- [ ] Code review completed

## 🎓 Pattern Documentation Structure

Each refactored file will generate:
1. **Before/After Diagram**: Visual representation
2. **Responsibility Matrix**: Detailed breakdown
3. **Migration Guide**: How to apply pattern
4. **Test Strategy**: How to verify equivalence
5. **Lessons Learned**: Pitfalls and solutions

---

**Status**: 📋 Planning Complete - Ready for Implementation
**Next**: Phase 3.2 - Detailed Responsibility Decomposition
