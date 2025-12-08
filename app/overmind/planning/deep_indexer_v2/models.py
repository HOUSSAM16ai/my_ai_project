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
    total_loc: int = 0
    total_functions: int = 0
    total_classes: int = 0
    avg_function_complexity: float = 0.0
    max_function_complexity: int = 0
    hotspots: list[Any] = field(default_factory=list)
    max_function_complexity_ref: str | None = None
    std_function_complexity: float = 0.0


@dataclass
class FileMetric:
    path: str
    loc: int
    function_count: int
    class_count: int
    avg_function_complexity: float
    max_function_complexity: int
    tags: list[str]
    layer: str
    entrypoint: bool
    file_hash: str


@dataclass
class IndexResult:
    files_scanned: int
    global_metrics: GlobalMetrics
    file_metrics: list[FileMetric]
    layers: dict[str, list[str]]
    modules: list[Any] = field(default_factory=list)
    dependencies: dict[str, Any] = field(default_factory=dict)
    functions: list[Any] = field(default_factory=list)
    service_candidates: list[str] = field(default_factory=list)
