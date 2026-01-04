"""أداة تدقيق شاملة لضمان توحيد التوثيق والتصميم عبر المشروع بالكامل."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

IGNORED_FOLDERS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "venv",
    ".venv",
    "node_modules",
}


@dataclass
class DocstringReport:
    """يوفر هذا التقرير رؤية مفصلة حول مستوى الالتزام بالمعايير في كل ملف."""

    file_path: Path
    missing_module_docstring: bool
    functions_missing_doc: list[str]
    classes_missing_doc: list[str]
    functions_missing_annotations: list[str]


@dataclass
class AuditSummary:
    """يجمع هذا الملخص النتائج الكاملة لعملية التدقيق لكل الملفات المفحوصة."""

    total_files: int
    files_with_issues: int
    docstring_reports: list[DocstringReport]
    design_reports: list["DesignReport"]
    duplicate_functions: list["DuplicateSignature"]


@dataclass
class DesignReport:
    """يوثق الانحرافات العملية عن مبادئ SOLID وKISS وDRY."""

    file_path: Path
    long_functions: list[str]
    complex_functions: list[str]
    side_effect_functions: list[str]


@dataclass
class DuplicateSignature:
    """يمثل مقطعاً وظيفياً مكرراً يعارض مبدأ DRY."""

    signature: str
    occurrences: list[str]


@dataclass
class FunctionObservation:
    """يصف خصائص تابع مفحوصة لدعم تحليلات التصميم."""

    identifier: str
    fingerprint: str | None


def gather_python_files(root: Path) -> list[Path]:
    """يجمع جميع ملفات بايثون القابلة للتدقيق مع استثناء المجلدات المتجاهلة."""

    candidates: Iterable[Path] = root.rglob("*.py")
    return [path for path in candidates if not _is_ignored(path)]


def _is_ignored(path: Path) -> bool:
    """يتحقق من ضرورة استبعاد المسار بناءً على المجلدات المتجاهلة."""

    return any(part in IGNORED_FOLDERS for part in path.parts)


def inspect_file(file_path: Path) -> DocstringReport:
    """يفحص ملفاً واحداً لرصد غياب التوثيق أو التعليقات التوضيحية للأنواع."""

    source_text = file_path.read_text(encoding="utf-8")
    module_node = ast.parse(source_text, filename=str(file_path))

    missing_module_docstring = ast.get_docstring(module_node) is None
    functions_missing_doc: list[str] = []
    classes_missing_doc: list[str] = []
    functions_missing_annotations: list[str] = []

    for node in ast.walk(module_node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node) is None:
                functions_missing_doc.append(node.name)
            if _function_missing_annotations(node):
                functions_missing_annotations.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if ast.get_docstring(node) is None:
                classes_missing_doc.append(node.name)

    return DocstringReport(
        file_path=file_path,
        missing_module_docstring=missing_module_docstring,
        functions_missing_doc=functions_missing_doc,
        classes_missing_doc=classes_missing_doc,
        functions_missing_annotations=functions_missing_annotations,
    )


def inspect_design(file_path: Path, max_lines: int, max_complexity: int) -> tuple[DesignReport, list[FunctionObservation]]:
    """يفحص التوازن التصميمي للتوابع ضمن الملف وفق مبادئ SOLID/KISS/DRY."""

    source_text = file_path.read_text(encoding="utf-8")
    module_node = ast.parse(source_text, filename=str(file_path))

    long_functions: list[str] = []
    complex_functions: list[str] = []
    side_effect_functions: list[str] = []
    observations: list[FunctionObservation] = []

    for node in ast.walk(module_node):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        identifier = f"{file_path}:{node.name}:{node.lineno}"
        length = _function_length(node)
        complexity = _function_complexity(node)
        fingerprint = _function_fingerprint(node, source_text)
        has_side_effects = _function_has_side_effects(node)

        if length > max_lines:
            long_functions.append(f"{node.name} (طول {length} سطر)")
        if complexity > max_complexity:
            complex_functions.append(f"{node.name} (تعقيد {complexity})")
        if has_side_effects:
            side_effect_functions.append(f"{node.name} (آثار جانبية)")

        observations.append(FunctionObservation(identifier=identifier, fingerprint=fingerprint))

    design_report = DesignReport(
        file_path=file_path,
        long_functions=long_functions,
        complex_functions=complex_functions,
        side_effect_functions=side_effect_functions,
    )
    return design_report, observations


def _function_missing_annotations(node: ast.AST) -> bool:
    """يتحقق من اكتمال التعليقات التوضيحية للوسائط والقيم المعادة."""

    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False

    arg_nodes = list(node.args.posonlyargs + node.args.args + node.args.kwonlyargs)
    if node.args.vararg is not None:
        arg_nodes.append(node.args.vararg)
    if node.args.kwarg is not None:
        arg_nodes.append(node.args.kwarg)

    significant_args = [arg for arg in arg_nodes if arg.arg not in {"self", "cls"}]
    missing_argument_annotations = any(argument.annotation is None for argument in significant_args)
    missing_return_annotation = node.returns is None
    return missing_argument_annotations or missing_return_annotation


def _function_length(node: ast.AST) -> int:
    """يقيس طول التابع بالأسطر لدعم مبدأ KISS."""

    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return 0
    if not node.body:
        return 0
    end_line = max(getattr(child, "end_lineno", node.lineno) for child in ast.walk(node))
    return end_line - node.lineno + 1


def _function_complexity(node: ast.AST) -> int:
    """يحسب تعقيداً تقريبياً بناءً على عدد التفرعات والتكرار."""

    complexity_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.BoolOp,
        ast.With,
        ast.Match,
        ast.IfExp,
        ast.ListComp,
        ast.DictComp,
        ast.SetComp,
        ast.GeneratorExp,
    )
    return sum(isinstance(child, complexity_nodes) for child in ast.walk(node))


def _function_has_side_effects(node: ast.AST) -> bool:
    """يرصد استدعاءات I/O أو تلاعبات قد تحتاج لعزل عن اللب الوظيفي."""

    side_effect_calls = {"print", "open", "requests", "logging", "subprocess", "Path"}
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name) and child.func.id in side_effect_calls:
                return True
            if isinstance(child.func, ast.Attribute) and child.func.attr in side_effect_calls:
                return True
    return False


def _function_fingerprint(node: ast.AST, source_text: str) -> str | None:
    """ينشئ بصمة نصية للجسم لتحديد المكررات (DRY)."""

    raw_source = ast.get_source_segment(source_text, node)
    if raw_source is None:
        try:
            raw_source = ast.unparse(node)
        except Exception:  # noqa: BLE001
            return None

    normalized_lines = [line.strip() for line in raw_source.splitlines() if line.strip()]
    if not normalized_lines:
        return None
    return "|".join(normalized_lines)


def _register_fingerprints(registry: dict[str, list[str]], observations: list[FunctionObservation]) -> None:
    """يحفظ البصمات المكررة لتقييم مبدأ DRY عبر المشروع."""

    for observation in observations:
        if observation.fingerprint is None:
            continue
        registry.setdefault(observation.fingerprint, []).append(observation.identifier)


def build_summary(files: list[Path], max_lines: int, max_complexity: int) -> AuditSummary:
    """يولد ملخصاً شاملاً لنتائج التدقيق لكل الملفات المحددة."""

    docstring_reports: list[DocstringReport] = []
    design_reports: list[DesignReport] = []
    fingerprints: dict[str, list[str]] = {}

    issue_paths: set[Path] = set()

    for path in files:
        doc_report = inspect_file(path)
        design_report, observations = inspect_design(path, max_lines=max_lines, max_complexity=max_complexity)
        docstring_reports.append(doc_report)
        design_reports.append(design_report)
        _register_fingerprints(fingerprints, observations)

        if _has_issues(doc_report) or _design_has_issues(design_report):
            issue_paths.add(path)

    files_with_issues = len(issue_paths)
    duplicate_functions = [
        DuplicateSignature(signature=signature, occurrences=locations)
        for signature, locations in fingerprints.items()
        if len(locations) > 1
    ]

    return AuditSummary(
        total_files=len(files),
        files_with_issues=files_with_issues,
        docstring_reports=docstring_reports,
        design_reports=design_reports,
        duplicate_functions=duplicate_functions,
    )


def _has_issues(report: DocstringReport) -> bool:
    """يحدد ما إذا كان التقرير يحتوي على أي مخالفات موثقة."""

    return (
        report.missing_module_docstring
        or bool(report.functions_missing_doc)
        or bool(report.classes_missing_doc)
        or bool(report.functions_missing_annotations)
    )


def _design_has_issues(report: DesignReport) -> bool:
    """يحدد وجود مخالفات تصميمية ملحوظة."""

    return bool(report.long_functions or report.complex_functions or report.side_effect_functions)


def render_report(summary: AuditSummary, limit: int | None) -> str:
    """ينشئ تقريراً نصياً منسقاً يبرز المخالفات المكتشفة."""

    header = [
        "تقرير التدقيق المعياري",
        f"إجمالي الملفات المفحوصة: {summary.total_files}",
        f"عدد الملفات التي تحتوي على مخالفات: {summary.files_with_issues}",
    ]

    details: list[str] = []
    displayed = 0
    for report in summary.docstring_reports:
        if not _has_issues(report):
            continue
        if limit is not None and displayed >= limit:
            break
        details.append(str(report.file_path))
        if report.missing_module_docstring:
            details.append("  - يفتقد إلى توثيق عام على مستوى الملف")
        if report.functions_missing_doc:
            missing_functions = ", ".join(report.functions_missing_doc)
            details.append(f"  - توابع بلا توثيق: {missing_functions}")
        if report.classes_missing_doc:
            missing_classes = ", ".join(report.classes_missing_doc)
            details.append(f"  - أصناف بلا توثيق: {missing_classes}")
        if report.functions_missing_annotations:
            missing_annotations = ", ".join(report.functions_missing_annotations)
            details.append(f"  - توابع بلا تعليقات توضيحية للأنواع: {missing_annotations}")
        displayed += 1

    design_details: list[str] = []
    design_displayed = 0
    for design_report in summary.design_reports:
        if not _design_has_issues(design_report):
            continue
        if limit is not None and design_displayed >= limit:
            break
        design_details.append(str(design_report.file_path))
        if design_report.long_functions:
            long_functions = ", ".join(design_report.long_functions)
            design_details.append(f"  - توابع طويلة تتعارض مع KISS: {long_functions}")
        if design_report.complex_functions:
            complex_functions = ", ".join(design_report.complex_functions)
            design_details.append(f"  - تعقيد مرتفع يتعارض مع SOLID: {complex_functions}")
        if design_report.side_effect_functions:
            impure_functions = ", ".join(design_report.side_effect_functions)
            design_details.append(f"  - توابع ذات آثار جانبية تحتاج لعزل: {impure_functions}")
        design_displayed += 1

    duplicate_details: list[str] = []
    for duplicate in summary.duplicate_functions:
        if limit is not None and len(duplicate_details) >= (limit * 2 if limit else 0):
            break
        joined_locations = "; ".join(duplicate.occurrences)
        duplicate_details.append(
            f"مقاطع مكررة (يعارض DRY) بتوقيع {duplicate.signature}: {joined_locations}"
        )

    footer = []
    if limit is not None:
        hidden_doc = max(summary.files_with_issues - displayed, 0)
        hidden_design = max(summary.files_with_issues - design_displayed, 0)
        hidden_duplicates = max(len(summary.duplicate_functions) - len(duplicate_details), 0)
        hidden_total = hidden_doc + hidden_design + hidden_duplicates
        if hidden_total > 0:
            footer.append(
                f"تم إخفاء {hidden_total} نتيجة لتقليل الضوضاء. استخدم --limit 0 لإظهار الجميع."
            )

    sections = header + details + design_details + duplicate_details + footer
    return "\n".join(sections)


def parse_arguments() -> argparse.Namespace:
    """يحلل خيارات سطر الأوامر لتهيئة معلمات التدقيق."""

    parser = argparse.ArgumentParser(description="تدقيق شامل للتوثيق وتعليقات الأنواع")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="مسار جذر المشروع المراد فحصه")
    parser.add_argument("--limit", type=int, default=20, help="عدد الملفات التي سيتم عرض تفاصيلها (0 لإظهار الجميع)")
    parser.add_argument("--max-lines", type=int, default=80, help="أقصى طول للتوابع قبل اعتبارها مخالفة لمبدأ KISS")
    parser.add_argument(
        "--max-complexity",
        type=int,
        default=12,
        help="أقصى تعقيد للتوابع قبل اعتبارها مخالفة لمبدأ SOLID (مسؤولية واحدة)",
    )
    return parser.parse_args()


def main() -> None:
    """ينفذ تدقيقاً شاملاً وفق المعايير الموضوعة على كامل المشروع."""

    arguments = parse_arguments()
    target_root = arguments.root.resolve()
    limit = arguments.limit if arguments.limit != 0 else None

    files = gather_python_files(target_root)
    summary = build_summary(files, max_lines=arguments.max_lines, max_complexity=arguments.max_complexity)
    report_text = render_report(summary, limit)
    print(report_text)

    if summary.files_with_issues > 0:
        exit(1)


if __name__ == "__main__":
    main()
