"""
Adaptive Multi-Pass Architecture Planner (Epic Final Edition)
=============================================================
File      : app/overmind/planning/multi_pass_arch_planner.py
Class     : AdaptiveMultiPassArchPlanner  (aliased as MultiPassArchPlanner)
Version   : 0.9.0-epic-l5
Status    : Experimental / Advanced (production_ready=False)
Pattern   : STRICT t\\d{2} task IDs for placeholder interpolation compatibility.

PURPOSE
-------
Generates a deeply structured, bilingual (English → Arabic) architecture dossier with:
  * Repository discovery (directory + core files)
  * Structural index simulation (or enrichment via injected deep_context)
  * Semantic structural JSON (layers / services / hotspots / risks / refactor ops)
  * JSON validation stage
  * Multiple focused sections (t11..t18)
  * Gap audit + gap fill
  * Cross-link synthesis
  * QA metrics (coverage_ratio, bilingual_completeness, etc.)
  * Optional executive summary polish
  * Final merged dossier (dynamic filename supported)

PLACEHOLDER COMPAT
------------------
All tasks use IDs: t01..t24 (and no alphanumeric suffix).
Plan content interpolation expects patterns: {{t\\d{2}.content}} or {{t\\d{2}.answer}}.
We consistently use:
  - {{tXX.answer}} for LLM (generic_think) outputs
  - {{tXX.content}} for raw file tool output ONLY if needed
Interpolation occurs before tool execution of write_file on final merge.

TASK GRAPH (High-Level)
-----------------------
(Discovery)
  t01 list_dir
  t02 read docker-compose.yml
  t03 read Dockerfile
  t04 read requirements.txt
  t05 read config.py
  t06 read run.py
  t07 read README.md

(Index + Semantics)
  t08 structural index synthesis (uses deep_context if available else simulate)
  t09 semantic structural JSON (strict schema request)
  t10 semantic JSON validation / correction

(Sections)
  t11 Executive Summary
  t12 Layered Architecture
  t13 Service Inventory
  t14 Data Flow
  t15 Hotspots & Complexity
  t16 Refactor & Improvement Plan
  t17 Risk Matrix & Resilience
  t18 Arabic Mirror Sections

(Audit / Enrichment / Consolidation)
  t19 Gap Audit
  t20 Gap Fill
  t21 Synthesis (cross-links)
  t22 QA Metrics JSON
  t23 (Optional) Executive Summary Polish (env-controlled)
  t24 Final Merge (writes dossier) – merges improved summary if polish enabled else original

ENV FLAGS
---------
ARCH_PLANNER_ENABLE_POLISH=1|0         Enable polish stage (t23) -> merged in t24
ARCH_PLANNER_OUTPUT_FILE=FILENAME.md   Override final output file name
ARCH_PLANNER_DEFAULT_FILE=ARCHITECTURE_overmind.md (fallback)
ARCH_PLANNER_MIN_COVERAGE=0.55         Threshold guiding polish logic
ARCH_PLANNER_MIN_BILINGUAL=0.80        Threshold guiding polish logic
ARCH_PLANNER_MAX_CORE_BYTES=120000     Per core file read limit
ARCH_PLANNER_SEM_JSON_VALIDATE=1|0     Enable JSON validation step (t10)
ARCH_PLANNER_FORCE_ARABIC=0|1          Future hook (not used yet)
ARCH_PLANNER_FILE_FROM_OBJECTIVE=1|0   Parse pattern FILE:Name.ext from objective if present

DYNAMIC OUTPUT FILENAME
-----------------------
Priority:
  1) Explicit pattern in objective: FILE:SomeName.md (if ARCH_PLANNER_FILE_FROM_OBJECTIVE=1)
  2) Env ARCH_PLANNER_OUTPUT_FILE
  3) Env ARCH_PLANNER_DEFAULT_FILE (defaults to ARCHITECTURE_overmind.md)

DEEP CONTEXT INJECTION
----------------------
If deep_context dict is passed, t08 prompt includes:
  files_scanned, hotspots_count, optional layers/services/entrypoints if present.

JSON VALIDATION (t10)
---------------------
Re-processes t09 output to ensure strict JSON shape:
  {layers:[], services:[], hotspots:[], risks:[], refactor_opportunities:[]}
If invalid, requests corrected JSON only.

POLISH STAGE (t23)
------------------
If enabled and thresholds from QA (t22) not met:
  Rewrites executive summary (English + short Arabic reinforcement).
Final Merge (t24) conditionally embeds:
  - {{t23.answer}} if polish enabled
  - else {{t11.answer}} (original executive summary)

SAFETY & DESIGN CHOICES
-----------------------
- Each task independent except required DAG edges.
- Uses .answer for LLM tasks (generic_think returns answer).
- Escapes user { } braces in objective to avoid placeholder collisions.
- Soft-missing reads so pipeline is resilient if core files are absent.
- Straight-line numeric ID growth simplifies insertion of new tasks.

EXTENSIBILITY NOTES
-------------------
Add retrieval tasks (e.g., code_search_lexical) by inserting between t07 and t08 with new IDs
like t07a (not allowed due to regex) → instead shift future tasks and keep numeric pattern.
To extend, bump version to avoid plan hash reuse.

"""

from __future__ import annotations

import os
import time
from typing import Any, ClassVar

from .base_planner import BasePlanner

# =============================== CONFIG LISTS ===============================

CORE_FILES = [
    ("t02", "docker-compose.yml"),
    ("t03", "Dockerfile"),
    ("t04", "requirements.txt"),
    ("t05", "config.py"),
    ("t06", "run.py"),
    ("t07", "README.md"),
]

SECTION_SPECS = [
    (
        "t11",
        "Executive Summary",
        "High-level purpose, current maturity, constraints, major value streams.",
    ),
    (
        "t12",
        "Layered Architecture",
        "List layers, boundaries, inbound/outbound responsibilities, interface clarity.",
    ),
    (
        "t13",
        "Service Inventory",
        "Enumerate services/modules: name, role, critical interactions, coupling indicators.",
    ),
    (
        "t14",
        "Data Flow",
        "Primary request flow, async/event pipelines, ingress/egress channels, data transformation hotspots.",
    ),
    (
        "t15",
        "Hotspots & Complexity",
        "List complex/large files, duplication hints, performance bottlenecks, potential instability.",
    ),
    (
        "t16",
        "Refactor & Improvement Plan",
        "Phased actionable plan: quick wins vs deeper refactors; expected impact.",
    ),
    (
        "t17",
        "Risk Matrix & Resilience",
        "Failure modes, severity, likelihood, mitigation, resilience posture gaps.",
    ),
    (
        "t18",
        "Arabic Mirror Sections",
        "Arabic concise reflection of English insights (not literal translation).",
    ),
]


# =============================== PLANNER CLASS ==============================


class AdaptiveMultiPassArchPlanner(BasePlanner):
    """
    Epic Adaptive Multi-Pass Architecture Planner
    Builds a deeply structured bilingual architecture dossier with audits and QA.
    """

    name = "adaptive_multi_pass_arch_planner"
    version = "0.9.0-epic-l5"
    production_ready = False
    capabilities: ClassVar[set[str]] = {
        "architecture",
        "multi_stage",
        "llm",
        "deep_index",
        "adaptive",
        "qa",
        "bilingual",
    }

    # ------------------------------------------------------------------ PUBLIC ENTRY
    def instrumented_generate(self, objective: str, context=None, deep_context=None):
        t0 = time.perf_counter()
        plan = self._build_plan(objective=objective, deep_context=deep_context)
        meta = {
            "planner": self.name,
            "version": self.version,
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "node_count": len(getattr(plan, "tasks", [])),
            "deep_context_used": bool(deep_context),
            "sections_count": len(SECTION_SPECS),
            "has_polish": self._is_polish_enabled(),
            "semantic_json_validation": self._is_semantic_validation_enabled(),
            "target_file": self._detect_target_file(objective),
        }
        return {"plan": plan, "meta": meta}

    # ------------------------------------------------------------------ CORE BUILD
    def _build_plan(self, objective: str, deep_context: dict[str, Any] | None):
        from app.overmind.planning.schemas import MissionPlanSchema, MissionTaskSchema

        safe_objective = self._escape_braces(objective)
        enable_polish = self._is_polish_enabled()
        validate_semantic = self._is_semantic_validation_enabled()
        target_file = self._detect_target_file(objective)

        max_core_bytes = int(os.getenv("ARCH_PLANNER_MAX_CORE_BYTES", "120000"))
        min_cov_threshold = float(os.getenv("ARCH_PLANNER_MIN_COVERAGE", "0.55"))
        min_bi_threshold = float(os.getenv("ARCH_PLANNER_MIN_BILINGUAL", "0.80"))

        tasks: list[MissionTaskSchema] = []

        # ------------------- t01: Repo listing
        tasks.append(
            MissionTaskSchema(
                task_id="t01",
                description="List repository root (structural discovery).",
                tool_name="list_dir",
                tool_args={"path": ".", "max_entries": 800},
                dependencies=[],
            )
        )

        # ------------------- t02..t07: Core file reads (soft-missing)
        for tid, path in CORE_FILES:
            tasks.append(
                MissionTaskSchema(
                    task_id=tid,
                    description=f"Read core file {path} (soft-missing).",
                    tool_name="read_file",
                    tool_args={"path": path, "ignore_missing": True, "max_bytes": max_core_bytes},
                    dependencies=[],
                )
            )

        # ------------------- t08: Structural index (simulate or enriched)
        if deep_context and isinstance(deep_context, dict):
            dc_lines = [
                f"FilesScanned: {deep_context.get('files_scanned')}",
                f"HotspotsCount: {deep_context.get('hotspots_count')}",
            ]
            if deep_context.get("layers"):
                dc_lines.append("Layers: " + ", ".join(deep_context.get("layers")[:8]))
            if deep_context.get("services"):
                dc_lines.append("Services: " + ", ".join(deep_context.get("services")[:10]))
            if deep_context.get("entrypoints"):
                dc_lines.append("Entrypoints: " + ", ".join(deep_context.get("entrypoints")[:6]))
            if deep_context.get("build_ms") is not None:
                dc_lines.append(f"BuildMS: {deep_context.get('build_ms')}")
            dc_block = "\n".join(dc_lines)
            structural_prompt = (
                "Real deep context provided below. Synthesize concise structural bullets:\n"
                " - Layers & their responsibilities\n"
                " - Key services & coupling hints\n"
                " - Potential hotspots / complexity vectors\n"
                " - Duplication / risk signals\n\n"
                f"DEEP_CONTEXT:\n{dc_block}\n\n"
                "ROOT LISTING:\n{{t01.content}}\n\n"
                "CORE FILE SNAPSHOTS (truncated if large):\n"
                + "\n".join(f"{tid}: {{{{{tid}.content}}}}" for tid, _ in CORE_FILES)
            )
        else:
            structural_prompt = (
                "No precomputed deep context. Infer a pseudostructural index from listing + core files.\n"
                "Produce structured bullet clusters covering: layers, major services/modules, probable hotspots, duplication, initial refactor hints.\n\n"
                "ROOT LISTING:\n{{t01.content}}\n\n"
                "CORE FILE SNAPSHOTS:\n"
                + "\n".join(f"{tid}: {{{{{tid}.content}}}}" for tid, _ in CORE_FILES)
            )

        tasks.append(
            MissionTaskSchema(
                task_id="t08",
                description="Structural index synthesis (simulated or enriched).",
                tool_name="generic_think",
                tool_args={"prompt": structural_prompt},
                dependencies=["t01"] + [tid for tid, _ in CORE_FILES],
            )
        )

        # ------------------- t09: Semantic JSON request
        semantic_json_prompt = (
            "From structural index below produce STRICT JSON ONLY (no markdown, no prose):\n"
            "{{t08.answer}}\n\n"
            "Schema keys (ALL required, empty arrays if unknown):\n"
            "layers, services, hotspots, risks, refactor_opportunities\n\n"
            "Return ONLY JSON."
        )
        tasks.append(
            MissionTaskSchema(
                task_id="t09",
                description="Semantic structural JSON (raw attempt).",
                tool_name="generic_think",
                tool_args={"prompt": semantic_json_prompt},
                dependencies=["t08"],
            )
        )

        # ------------------- t10: Validation / correction (optional)
        if validate_semantic:
            validation_prompt = (
                "Validate or correct the semantic JSON below. Ensure keys EXACTLY:\n"
                "layers, services, hotspots, risks, refactor_opportunities\n"
                "If invalid, repair silently.\n"
                "Return ONLY valid JSON.\n\nRAW:\n{{t09.answer}}"
            )
            tasks.append(
                MissionTaskSchema(
                    task_id="t10",
                    description="Semantic JSON validation & normalization.",
                    tool_name="generic_think",
                    tool_args={"prompt": validation_prompt},
                    dependencies=["t09"],
                )
            )
            semantic_source_id = "t10"
        else:
            semantic_source_id = "t09"

        # ------------------- t11..t18: Section Drafts
        for tid, title, guidance in SECTION_SPECS:
            section_prompt = (
                f"OBJECTIVE:\n{safe_objective}\n\n"
                f"STRUCTURAL INDEX (raw):\n{{t08.answer}}\n\n"
                f"SEMANTIC JSON (validated if available):\n{{{semantic_source_id}.answer}}\n\n"
                f"Write section: {title}\n"
                f"Guidance: {guidance}\n"
                "- Use concise headings / bullets.\n"
                "- Reference specific services/files when adding value.\n"
                "- Avoid repeating earlier sections verbatim.\n"
                "- If data uncertainty: note assumptions.\n"
                "- Target ≤ ~450 words.\n"
            )
            if tid == "t18":
                section_prompt += "\nArabic Mirror: Provide an Arabic concise perspective (موجز تحليلي) distilling key English architectural insights."
            tasks.append(
                MissionTaskSchema(
                    task_id=tid,
                    description=f"Draft section: {title}",
                    tool_name="generic_think",
                    tool_args={"prompt": section_prompt},
                    dependencies=[semantic_source_id],
                )
            )

        # ------------------- t19: Gap Audit
        section_refs_block = "\n\n".join(
            f"== {title} ==\n{{{{{tid}.answer}}}}" for tid, title, _ in SECTION_SPECS
        )
        gap_audit_prompt = (
            f"SEMANTIC JSON:\n{{{semantic_source_id}.answer}}\n\n"
            "SECTIONS:\n" + section_refs_block + "\n\nPerform coverage audit:\n"
            "- missing_services: services in JSON not referenced in any section\n"
            "- missing_layers: layers not referenced\n"
            "- missing_hotspots: hotspots not addressed\n"
            "- missing_risks: risks not described\n"
            "- notes: advisory strings\n"
            "Return STRICT JSON:\n"
            "{missing_services:[], missing_layers:[], missing_hotspots:[], missing_risks:[], notes:[]}"
        )
        tasks.append(
            MissionTaskSchema(
                task_id="t19",
                description="Gap audit vs semantic JSON.",
                tool_name="generic_think",
                tool_args={"prompt": gap_audit_prompt},
                dependencies=[tid for tid, _, _ in SECTION_SPECS],
            )
        )

        # ------------------- t20: Gap Fill
        gap_fill_prompt = (
            "GAP JSON:\n{{t19.answer}}\n\n"
            "If every array empty → respond EXACTLY 'NO_GAPS'.\n"
            "Else produce bullet expansions addressing each missing element. Include concise English + optional inline Arabic hints."
        )
        tasks.append(
            MissionTaskSchema(
                task_id="t20",
                description="Gap fill expansions.",
                tool_name="generic_think",
                tool_args={"prompt": gap_fill_prompt},
                dependencies=["t19"],
            )
        )

        # ------------------- t21: Synthesis
        synthesis_prompt = (
            "Synthesize integrated architectural perspective:\n"
            "Sections:\n" + section_refs_block + "\n\n"
            "Gap Fill:\n{{t20.answer}}\n\n"
            "Produce ~400 word synthesis including:\n"
            "- Cross-layer dependency map\n"
            "- Service interaction highlights\n"
            "- Risk propagation chain\n"
            "- Unified phased refactor priority\n"
            "- Key resilience and performance improvement levers"
        )
        tasks.append(
            MissionTaskSchema(
                task_id="t21",
                description="Cross-link synthesis.",
                tool_name="generic_think",
                tool_args={"prompt": synthesis_prompt},
                dependencies=[tid for tid, _, _ in SECTION_SPECS] + ["t20"],
            )
        )

        # ------------------- t22: QA Metrics
        qa_prompt = (
            "Compute STRICT JSON metrics (only JSON, no prose):\n"
            f"SEMANTIC JSON:\n{{{semantic_source_id}.answer}}\n\n"
            "SYNTHESIS:\n{{t21.answer}}\n\n"
            "SECTIONS (for counting references only):\n" + section_refs_block + "\n\n"
            "Rules:\n"
            "- word_count: approximate total English words in t11..t17 + synthesis.\n"
            "- referenced_files_count: distinct file or module names cited (infer heuristically).\n"
            "- coverage_ratio: (mentioned services) / (total semantic JSON services).\n"
            "- bilingual_completeness: heuristic ∈ [0,1] for adequacy of Arabic mirror section.\n"
            "- notes: short advisory strings.\n"
            "Return JSON EXACT KEYS:\n"
            "{word_count:int, referenced_files_count:int, coverage_ratio:float, bilingual_completeness:float, notes:[]}"
        )
        tasks.append(
            MissionTaskSchema(
                task_id="t22",
                description="QA coverage metrics.",
                tool_name="generic_think",
                tool_args={"prompt": qa_prompt},
                dependencies=["t21"],
            )
        )

        # ------------------- t23: Optional Polish (Executive Summary refinement)
        if enable_polish:
            polish_prompt = (
                f"QA JSON:\n{{t22.answer}}\n\n"
                f"COVERAGE_THRESHOLD={min_cov_threshold} BILINGUAL_THRESHOLD={min_bi_threshold}\n"
                "Original Executive Summary:\n{{t11.answer}}\n\n"
                "If (coverage_ratio < COVERAGE_THRESHOLD) OR (bilingual_completeness < BILINGUAL_THRESHOLD):\n"
                "- Produce improved executive summary (English) + brief Arabic reinforcement (≠ literal translation).\n"
                "- Keep ≤ 380 words.\n"
                "Else respond EXACTLY: NO_POLISH_NEEDED"
            )
            tasks.append(
                MissionTaskSchema(
                    task_id="t23",
                    description="Executive Summary polish (conditional).",
                    tool_name="generic_think",
                    tool_args={"prompt": polish_prompt},
                    dependencies=["t22"],
                )
            )

        # ------------------- t24: Final Merge
        merge_content = self._final_merge_template(
            semantic_source_id=semantic_source_id, use_polish=enable_polish, target_file=target_file
        )
        merge_dependencies = ["t22"]
        if enable_polish:
            merge_dependencies.append("t23")

        tasks.append(
            MissionTaskSchema(
                task_id="t24",
                description="Write final bilingual architecture dossier with QA and (optional) polished summary.",
                tool_name="write_file",
                tool_args={"path": target_file, "content": merge_content},
                dependencies=merge_dependencies,
            )
        )

        return MissionPlanSchema(objective=objective, tasks=tasks)

    # ------------------------------------------------------------------ UTILITIES

    @staticmethod
    def _escape_braces(text: str) -> str:
        # Avoid accidental placeholder collisions by replacing raw braces
        return text.replace("{", "〔").replace("}", "〕")

    @staticmethod
    def _is_polish_enabled() -> bool:
        return os.getenv("ARCH_PLANNER_ENABLE_POLISH", "0").lower() in ("1", "true", "yes")

    @staticmethod
    def _is_semantic_validation_enabled() -> bool:
        return os.getenv("ARCH_PLANNER_SEM_JSON_VALIDATE", "1").lower() in ("1", "true", "yes")

    @staticmethod
    def _detect_target_file(objective: str) -> str:
        # Priority: FILE:Name.ext in objective (if allowed) > ARCH_PLANNER_OUTPUT_FILE > ARCH_PLANNER_DEFAULT_FILE
        allow_obj = os.getenv("ARCH_PLANNER_FILE_FROM_OBJECTIVE", "1").lower() in (
            "1",
            "true",
            "yes",
        )
        default_file = os.getenv("ARCH_PLANNER_DEFAULT_FILE", "ARCHITECTURE_overmind.md")
        env_file = os.getenv("ARCH_PLANNER_OUTPUT_FILE", "").strip()
        candidate = None
        if allow_obj:
            import re

            m = re.search(r"FILE\s*:\s*([A-Za-z0-9_\-./]+)", objective, flags=re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
        if not candidate and env_file:
            candidate = env_file
        if not candidate:
            candidate = default_file
        # Ensure extension
        if "." not in os.path.basename(candidate):
            candidate += ".md"
        return candidate

    @staticmethod
    def _final_merge_template(semantic_source_id: str, use_polish: bool, target_file: str) -> str:
        """
        Build final dossier content string using placeholders.
        NOTE:
          - If polish enabled: Executive Summary uses t23.answer
          - Else: uses original t11.answer
        """
        exec_block = "{{t23.answer}}" if use_polish else "{{t11.answer}}"

        # Gap fill or NO_GAPS token included as-is.
        # All placeholders remain compliant with interpolation regex.
        sections = [
            "# EXECUTIVE SUMMARY",
            exec_block,
            "## LAYERED ARCHITECTURE",
            "{{t12.answer}}",
            "## SERVICE INVENTORY",
            "{{t13.answer}}",
            "## DATA FLOW",
            "{{t14.answer}}",
            "## HOTSPOTS & COMPLEXITY",
            "{{t15.answer}}",
            "## REFACTOR & IMPROVEMENT PLAN",
            "{{t16.answer}}",
            "## RISK MATRIX & RESILIENCE",
            "{{t17.answer}}",
            "## النسخة العربية (ملخص الأقسام)",
            "{{t18.answer}}",
            "## GAP FILL",
            "{{t20.answer}}",
            "## SYNTHESIS",
            "{{t21.answer}}",
            "## QA METRICS",
            "{{t22.answer}}",
            "",
            f"<!-- Generated by AdaptiveMultiPassArchPlanner v0.9.0 targeting file: {target_file} -->",
            f"<!-- Semantic JSON Source: {semantic_source_id} -->",
        ]
        return "\n".join(sections)


# Backward compatibility alias
MultiPassArchPlanner = AdaptiveMultiPassArchPlanner
