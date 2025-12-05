# Ultra-Hyper Planner Refactoring Blueprint (v8.0)

## Objective
Deconstruct the monolithic `llm_planner.py` (1700+ lines) into a "Hyper-Modular" atomic architecture to improve maintainability, testability, and scalability.

## Target Structure: `app/overmind/planning/hyper_planner/`

### 1. `config.py` (The Configuration Matrix)
**Responsibility:** Centralized configuration management.
- Extracts all `os.getenv` calls.
- Defines constants (e.g., `GLOBAL_TASK_CAP`, `PLANNER_VERSION`).
- Strictly typed settings using `pydantic` or `dataclasses` (or plain python classes if keeping dependencies low).

### 2. `utils.py` (The Utility Kernel)
**Responsibility:** Pure helper functions.
- Language detection (`_detect_lang`).
- Filename normalization (`_normalize_filename`).
- Text truncation and formatting.
- RegEx patterns (`FILENAME_PATTERNS`).

### 3. `prompts.py` (The Prompt Engineering Engine)
**Responsibility:** Dynamic prompt construction.
- `build_role_prompt`
- `build_section_prompt`
- `build_chunk_prompt`
- `build_final_wrap_prompt`
- Decouples logic from string templates.

### 4. `models.py` (The Semantic Schema)
**Responsibility:** Data structures.
- `PlannerError`, `PlanValidationError`.
- `PlannedTask` (if not imported from `schemas`).
- `MissionPlanSchema` (if not imported from `schemas`).

### 5. `features/` (The Feature Plugins)
**Responsibility:** Encapsulated logic for specific planner features.
- `repo_scanner.py`: Logic for `_add_repo_scan_tasks`.
- `deep_indexer.py`: Logic for `_attempt_deep_index` (wraps the external deep indexer).
- `file_generator.py`: Logic for `_add_file_generation_blocks`.

### 6. `core.py` (The Orchestration Nexus)
**Responsibility:** The `UltraHyperPlanner` class.
- Inherits from `BasePlanner`.
- Orchestrates the flow: Input -> Config -> Feature Handlers -> Plan.
- Error handling and fallback logic.

### 7. `__init__.py` (The Gateway)
- Exports `UltraHyperPlanner` for backward compatibility.

## Execution Protocol

1.  **Initialize**: Create directory structure.
2.  **Extract Config**: Move ENV logic to `config.py`.
3.  **Extract Utils**: Move helpers to `utils.py`.
4.  **Extract Prompts**: Move builders to `prompts.py`.
5.  **Extract Features**: Create feature modules.
6.  **Reassemble Core**: Rebuild `UltraHyperPlanner` in `core.py` using imports.
7.  **Bridge**: Update `llm_planner.py` to import from `hyper_planner`.
