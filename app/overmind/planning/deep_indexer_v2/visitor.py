import ast
from collections import Counter
from typing import Any

from .analysis import categorize, hash_norm_function
from .config import CONFIG
from .models import ClassInfo, FunctionInfo


class DeepIndexVisitor(ast.NodeVisitor):
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.functions: list[FunctionInfo] = []
        self.classes: list[ClassInfo] = []
        self.imports: list[str] = []
        self.call_counter: Counter = Counter()
        # Stack of function contexts: {name, lineno, end, hash, tags, complexity, recursive, calls_out}
        self.func_stack: list[dict[str, Any]] = []

    def _inc_complexity(self, amount: int = 1) -> None:
        for ctx in self.func_stack:
            ctx["complexity"] += amount

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        start = node.lineno
        end = getattr(node, "end_lineno", start)
        slice_src = "\n".join(self.lines[start - 1 : end])
        h = hash_norm_function(slice_src, CONFIG["DUP_HASH_PREFIX"])
        tags = categorize(slice_src)

        ctx = {
            "name": node.name,
            "lineno": start,
            "end_lineno": end,
            "loc": end - start + 1,
            "hash": h,
            "tags": tags,
            "complexity": 1,
            "recursive": False,
            "calls_out": [],
        }
        self.func_stack.append(ctx)

        self.generic_visit(node)

        finished_ctx = self.func_stack.pop()
        self.functions.append(
            FunctionInfo(
                name=finished_ctx["name"],
                lineno=finished_ctx["lineno"],
                end_lineno=finished_ctx["end_lineno"],
                loc=finished_ctx["loc"],
                hash=finished_ctx["hash"],
                complexity=finished_ctx["complexity"],
                recursive=finished_ctx["recursive"],
                tags=finished_ctx["tags"],
                calls_out=finished_ctx["calls_out"],
            )
        )

    def _visit_complexity_node(self, node: ast.AST, amount: int = 1) -> None:
        self._inc_complexity(amount)
        self.generic_visit(node)

    # Complexity increasers
    def visit_If(self, node: ast.If) -> None:
        self._visit_complexity_node(node)

    def visit_For(self, node: ast.For) -> None:
        self._visit_complexity_node(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_complexity_node(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_complexity_node(node)

    def visit_With(self, node: ast.With) -> None:
        self._visit_complexity_node(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_complexity_node(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_complexity_node(node)

    def visit_Match(self, node: ast.Match) -> None:
        self._visit_complexity_node(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._visit_complexity_node(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_complexity_node(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_complexity_node(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_complexity_node(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_complexity_node(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self._inc_complexity(max(1, len(node.values) - 1))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        fn_name = None
        if isinstance(node.func, ast.Name):
            fn_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            fn_name = node.func.attr

        if fn_name:
            self.call_counter[fn_name] += 1
            for ctx in self.func_stack:
                ctx["calls_out"].append(fn_name)
                if isinstance(node.func, ast.Name) and fn_name == ctx["name"]:
                    ctx["recursive"] = True

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        start = node.lineno
        end = getattr(node, "end_lineno", start)
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)
            else:
                bases.append(type(b).__name__)

        self.classes.append(
            ClassInfo(
                name=node.name,
                lineno=start,
                end_lineno=end,
                loc=(end - start + 1),
                bases=bases,
            )
        )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)
