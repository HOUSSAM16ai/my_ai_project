"""
مدقق المعايير الوكيلية.

ينفذ هذا السكريبت تحققاً برمجياً من الأدلة المرتبطة بمعايير الوكالة الخارقة،
ويخرج بتقرير واضح وإشارة فشل عند وجود نقص في الأدلة.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))

from app.core.agents.agentic_standards import (
    AgenticStandard,
    EvidenceRule,
    get_agentic_standards,
)


@dataclass(frozen=True)
class EvidenceResult:
    """نتيجة تحقق واحدة تربط القاعدة بحالة النجاح أو الفشل."""

    standard_id: str
    rule: EvidenceRule
    passed: bool
    message: str


def _load_ast(file_path: Path) -> ast.AST:
    """تحميل شجرة AST لملف محدد."""

    source_text = file_path.read_text(encoding="utf-8")
    return ast.parse(source_text, filename=str(file_path))


def _has_symbol(tree: ast.AST, symbol: str) -> bool:
    """التحقق من وجود صنف أو دالة باسم محدد."""

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return True
    return False


def _find_class(tree: ast.AST, class_name: str) -> ast.ClassDef | None:
    """إرجاع تعريف الصنف إذا وُجد."""

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


def _class_has_attribute(class_node: ast.ClassDef, attribute: str) -> bool:
    """يتحقق من وجود سمة ضمن جسم الصنف."""

    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == attribute:
                return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == attribute:
                    return True
    return False


def _class_has_method(class_node: ast.ClassDef, method_name: str) -> bool:
    """يتحقق من وجود تابع داخل الصنف."""

    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            return True
    return False


def _has_call(tree: ast.AST, symbol: str) -> bool:
    """يتحقق من وجود استدعاء لدالة أو مُنشئ باسم محدد."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == symbol:
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == symbol:
            return True
    return False


def _validate_rule(rule: EvidenceRule, standard_id: str) -> EvidenceResult:
    """ينفذ تحققاً واحداً وفق القاعدة المحددة."""

    target_path = REPO_ROOT / rule.path
    if not target_path.exists():
        return EvidenceResult(
            standard_id=standard_id,
            rule=rule,
            passed=False,
            message=f"الملف غير موجود: {rule.path}",
        )

    tree = _load_ast(target_path)

    if rule.kind == "file":
        return EvidenceResult(standard_id, rule, True, "تم العثور على الملف.")

    if rule.kind in {"class", "function"}:
        found = _has_symbol(tree, rule.symbol)
        return EvidenceResult(
            standard_id=standard_id,
            rule=rule,
            passed=found,
            message="تم العثور على الرمز." if found else "الرمز مفقود.",
        )

    if rule.kind == "method":
        if rule.owner is None:
            return EvidenceResult(
                standard_id=standard_id,
                rule=rule,
                passed=False,
                message="لم يتم تحديد الصنف المالك للطريقة.",
            )
        class_node = _find_class(tree, rule.owner)
        if class_node is None:
            return EvidenceResult(
                standard_id=standard_id,
                rule=rule,
                passed=False,
                message=f"الصنف {rule.owner} غير موجود.",
            )
        found = _class_has_method(class_node, rule.symbol)
        return EvidenceResult(
            standard_id=standard_id,
            rule=rule,
            passed=found,
            message="تم العثور على الطريقة." if found else "الطريقة مفقودة.",
        )

    if rule.kind == "attribute":
        if rule.owner is None:
            return EvidenceResult(
                standard_id=standard_id,
                rule=rule,
                passed=False,
                message="لم يتم تحديد الصنف المالك للسمة.",
            )
        class_node = _find_class(tree, rule.owner)
        if class_node is None:
            return EvidenceResult(
                standard_id=standard_id,
                rule=rule,
                passed=False,
                message=f"الصنف {rule.owner} غير موجود.",
            )
        found = _class_has_attribute(class_node, rule.symbol)
        return EvidenceResult(
            standard_id=standard_id,
            rule=rule,
            passed=found,
            message="تم العثور على السمة." if found else "السمة مفقودة.",
        )

    if rule.kind == "call":
        found = _has_call(tree, rule.symbol)
        return EvidenceResult(
            standard_id=standard_id,
            rule=rule,
            passed=found,
            message="تم العثور على الاستدعاء." if found else "الاستدعاء مفقود.",
        )

    return EvidenceResult(
        standard_id=standard_id,
        rule=rule,
        passed=False,
        message=f"نوع القاعدة غير مدعوم: {rule.kind}",
    )


def _validate_standard(standard: AgenticStandard) -> list[EvidenceResult]:
    """يفحص جميع القواعد المرتبطة بمعيار واحد."""

    return [_validate_rule(rule, standard.standard_id) for rule in standard.rules]


def _render_report(results: list[EvidenceResult]) -> str:
    """ينشئ تقريراً مفصلاً عن نتائج التحقق."""

    lines: list[str] = ["تقرير تدقيق المعايير الوكيلية", "-" * 72]
    for result in results:
        status = "✅" if result.passed else "❌"
        lines.append(
            f"{status} [{result.standard_id}] {result.rule.symbol} - {result.message} ({result.rule.path})"
        )
        if result.rule.description:
            lines.append(f"    ↳ {result.rule.description}")
    lines.append("-" * 72)
    return "\n".join(lines)


def run_audit() -> int:
    """يشغل عملية التدقيق ويعيد رمز الخروج المناسب."""

    standards = get_agentic_standards()
    results: list[EvidenceResult] = []
    for standard in standards:
        results.extend(_validate_standard(standard))

    report = _render_report(results)
    print(report)

    failures = [result for result in results if not result.passed]
    if failures:
        return 1
    return 0


def main() -> None:
    """نقطة الدخول لتنفيذ التدقيق."""

    raise SystemExit(run_audit())


if __name__ == "__main__":
    main()
