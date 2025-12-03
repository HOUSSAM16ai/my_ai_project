# 🎯 Phase 2 Implementation Plan - Large Function Refactoring
# خطة تطبيق المرحلة 2 - تجزئة الدوال الكبيرة

## 📊 Status Overview

### ✅ Completed (Phase 1)
- Created centralized infrastructure (AI client, circuit breaker, HTTP client)
- Reduced coupling through factory patterns
- Achieved 68% code reduction

### 🔄 In Progress (Phase 2)
Focus on breaking down large functions into smaller, manageable components.

## 🎯 Target Functions for Refactoring

### Priority 1: Multi-Pass Architecture Planner

**File:** `app/overmind/planning/multi_pass_arch_planner.py`

**Function:** `_build_plan` (275 lines)

**Refactoring Strategy:**
```python
# Current: One massive function
def _build_plan(self, objective, deep_context):
    # 275 lines of code...
    pass

# Target: Decomposed into logical units
class PlanBuilder:
    def build(self, objective, deep_context) -> MissionPlan:
        """Main orchestrator (~20 lines)"""
        config = self._load_configuration()
        tasks = []
        
        tasks.extend(self._create_discovery_tasks(config))
        tasks.extend(self._create_index_tasks(deep_context, config))
        tasks.extend(self._create_section_tasks(config))
        tasks.extend(self._create_audit_tasks(config))
        tasks.extend(self._create_finalization_tasks(config))
        
        return self._finalize_plan(objective, tasks)
    
    def _load_configuration(self) -> dict:
        """Load environment configuration (~15 lines)"""
        return {
            'enable_polish': self._is_polish_enabled(),
            'validate_semantic': self._is_semantic_validation_enabled(),
            'target_file': self._detect_target_file(objective),
            'max_core_bytes': int(os.getenv("ARCH_PLANNER_MAX_CORE_BYTES", "120000")),
            'min_cov_threshold': float(os.getenv("ARCH_PLANNER_MIN_COVERAGE", "0.55")),
            'min_bi_threshold': float(os.getenv("ARCH_PLANNER_MIN_BILINGUAL", "0.80")),
        }
    
    def _create_discovery_tasks(self, config) -> list[MissionTaskSchema]:
        """Create tasks t01-t07 (~40 lines)"""
        tasks = []
        # t01: Repository listing
        tasks.append(self._create_list_dir_task())
        # t02-t07: Core file reads
        tasks.extend(self._create_core_file_tasks(config['max_core_bytes']))
        return tasks
    
    def _create_index_tasks(self, deep_context, config) -> list[MissionTaskSchema]:
        """Create tasks t08-t10 (~50 lines)"""
        tasks = []
        # t08: Structural index
        tasks.append(self._create_structural_index_task(deep_context))
        # t09: Semantic JSON
        tasks.append(self._create_semantic_json_task())
        # t10: JSON validation (conditional)
        if config['validate_semantic']:
            tasks.append(self._create_json_validation_task())
        return tasks
    
    def _create_section_tasks(self, config) -> list[MissionTaskSchema]:
        """Create tasks t11-t18 (~60 lines)"""
        sections = [
            ('t11', 'Executive Summary'),
            ('t12', 'Layered Architecture'),
            ('t13', 'Service Inventory'),
            ('t14', 'Data Flow'),
            ('t15', 'Hotspots & Complexity'),
            ('t16', 'Refactor & Improvement Plan'),
            ('t17', 'Risk Matrix & Resilience'),
            ('t18', 'Arabic Mirror Sections'),
        ]
        return [self._create_section_task(tid, desc) for tid, desc in sections]
    
    def _create_audit_tasks(self, config) -> list[MissionTaskSchema]:
        """Create tasks t19-t22 (~40 lines)"""
        tasks = []
        tasks.append(self._create_gap_audit_task())
        tasks.append(self._create_gap_fill_task())
        tasks.append(self._create_synthesis_task())
        tasks.append(self._create_qa_metrics_task())
        return tasks
    
    def _create_finalization_tasks(self, config) -> list[MissionTaskSchema]:
        """Create tasks t23-t24 (~35 lines)"""
        tasks = []
        if config['enable_polish']:
            tasks.append(self._create_polish_task(config))
        tasks.append(self._create_final_merge_task(config))
        return tasks
    
    def _finalize_plan(self, objective, tasks) -> MissionPlan:
        """Create final MissionPlanSchema (~15 lines)"""
        return MissionPlanSchema(
            mission_id=str(uuid.uuid4()),
            objective=self._escape_braces(objective),
            tasks=tasks,
            metadata={
                "planner": "adaptive_multi_pass_arch",
                "version": "0.9.0",
                "task_count": len(tasks),
            }
        )
```

**Reduction:** 275 lines → ~80 lines main method + helper methods

### Priority 2: Other Large Functions

Additional functions to refactor (based on user's analysis):
1. `_full_graph_validation()` - 268 lines
2. `setup_error_handlers()` - 248 lines (may already be refactored)
3. `execute_task()` - 260 lines
4. `_execute_task_with_retry()` - 149 lines

## 📝 Implementation Approach

### Step 1: Extract Configuration Loading
Move environment variable loading to dedicated method.

### Step 2: Group Related Task Creation
Create separate methods for each logical group of tasks:
- Discovery tasks (t01-t07)
- Index tasks (t08-t10)
- Section tasks (t11-t18)
- Audit tasks (t19-t22)
- Finalization tasks (t23-t24)

### Step 3: Extract Helper Methods
Create reusable methods for:
- Creating task schemas
- Building prompts
- Formatting content

### Step 4: Maintain Backward Compatibility
Ensure the refactored code produces identical output.

## ✅ Benefits

1. **Readability:** Each method has a single, clear purpose
2. **Testability:** Individual methods can be unit tested
3. **Maintainability:** Easier to modify specific logic
4. **Reusability:** Helper methods can be used across planners
5. **Debugging:** Easier to identify issues in specific sections

## 🎯 Success Criteria

- [ ] Main method reduced to < 50 lines
- [ ] Each helper method < 50 lines
- [ ] All existing tests pass
- [ ] No change in output behavior
- [ ] Improved cyclomatic complexity

## 📅 Timeline

- **Configuration extraction:** 30 minutes
- **Task creation methods:** 2 hours
- **Helper methods:** 1 hour
- **Testing & validation:** 1 hour
- **Total:** ~4.5 hours

---

**Note:** This refactoring maintains 100% backward compatibility while significantly improving code maintainability and readability.

**Status:** Planning Complete ✅
**Next:** Implementation
