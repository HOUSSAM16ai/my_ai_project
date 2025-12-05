from dataclasses import dataclass


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
