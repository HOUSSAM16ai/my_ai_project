from dataclasses import dataclass, field
from typing import Any


@dataclass
class FunctionInfo:
    name: str
    lineno: int
    end_lineno: int
    loc: int
    hash: str
    complexity: int
    recursive: bool
    tags: list[str]
    calls_out: list[str]  # raw callee names (not resolved fully)


@dataclass
class ClassInfo:
    name: str
    lineno: int
    end_lineno: int
    loc: int
    bases: list[str]


@dataclass
class FileModule:
    path: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
    call_names: dict[str, int]
    file_hash: str
    error: str | None = None
    entrypoint: bool = False
    loc: int = 0


@dataclass
class GlobalMetrics:
    total_functions: int
    avg_function_complexity: float
    std_function_complexity: float
    max_function_complexity: int
    max_function_complexity_ref: str | None
    total_loc: int


@dataclass
class FileMetric:
    path: str
    file_hash: str
    loc: int
    function_count: int
    class_count: int
    avg_function_complexity: float
    max_function_complexity: int
    tags: list[str]
    layer: str
    entrypoint: bool


@dataclass
class IndexResult:
    files_scanned: int
    modules: list[dict[str, Any]]
    dependencies: dict[str, list[str]]
    functions: list[dict[str, Any]]
    function_call_frequency_top50: list[tuple[str, int]]
    complexity_hotspots_top50: list[dict[str, Any]]
    duplicate_function_bodies: dict[str, list[dict[str, Any]]]
    index_version: str
    file_metrics: list[FileMetric]
    layers: dict[str, list[str]]
    service_candidates: list[str]
    entrypoints: list[str]
    global_metrics: GlobalMetrics
    call_graph_edges_sample: list[dict[str, Any]]
    cache_used: bool
    cached_files: int
    changed_files: int
    skipped_large_files: list[str]
    generated_at: str
    config: dict[str, Any]
    version_details: dict[str, str]
    time_profile_ms: dict[str, float] = field(default_factory=dict)
