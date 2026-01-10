"""يوفر أدوات مسح شاملة لبنية المشروع من أجل تبسيط الصيانة وحذف الملفات الميتة."""
from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from json import dumps
from pathlib import Path


@dataclass
class NodeStats:
    """إحصاءات ملخصة لعقدة ضمن خريطة المستودع."""

    path: str
    kind: str
    size_bytes: int
    children: list[NodeStats]

    def to_dict(self) -> dict[str, object]:
        """يحوّل بيانات العقدة إلى قاموس صالح للتسلسل إلى JSON."""

        return {
            "path": self.path,
            "kind": self.kind,
            "size_bytes": self.size_bytes,
            "children": [child.to_dict() for child in self.children],
        }


def _should_skip(path: Path, include_hidden: bool) -> bool:
    """يتحقق ما إذا كان يجب استبعاد المسار الحالي من الفحص."""

    if include_hidden:
        return False
    return any(part.startswith(".") for part in path.parts)


def build_repository_map(
    root: Path, *, include_hidden: bool = False, max_depth: int | None = None
) -> NodeStats:
    """ينشئ خريطة شاملة لبنية المستودع بدءاً من الجذر المحدد."""

    normalized_root = root.resolve()
    if not normalized_root.exists():
        msg = f"المسار {normalized_root} غير موجود"
        raise FileNotFoundError(msg)

    def walk(current: Path, depth: int) -> NodeStats:
        is_directory = current.is_dir()
        kind = "directory" if is_directory else "file"
        if not is_directory:
            size = current.stat().st_size if current.exists() else 0
            return NodeStats(path=str(current.relative_to(normalized_root)), kind=kind, size_bytes=size, children=[])

        if max_depth is not None and depth >= max_depth:
            size = current.stat().st_size if current.exists() else 0
            return NodeStats(path=str(current.relative_to(normalized_root)), kind=kind, size_bytes=size, children=[])

        children: list[NodeStats] = []
        for child in sorted(current.iterdir()):
            if _should_skip(child.relative_to(normalized_root), include_hidden):
                continue
            children.append(walk(child, depth + 1))

        total_size = sum(child.size_bytes for child in children)
        return NodeStats(path=str(current.relative_to(normalized_root)), kind=kind, size_bytes=total_size, children=children)

    return walk(normalized_root, 0)


def summarize(node: NodeStats, predicate: Callable[[NodeStats], bool]) -> list[NodeStats]:
    """يستخرج قائمة بالعُقد التي تحقق شرط التصفية للمراجعة السريعة."""

    matches: list[NodeStats] = []
    if predicate(node):
        matches.append(node)
    for child in node.children:
        matches.extend(summarize(child, predicate))
    return matches


def emit_repository_map(root: Path, *, include_hidden: bool = False, max_depth: int | None = None) -> str:
    """يرجع تمثيلاً JSON لخريطة المستودع لتسهيل قراءتها من أدوات خارجية."""

    repository_map = build_repository_map(root, include_hidden=include_hidden, max_depth=max_depth)
    return dumps(repository_map.to_dict(), ensure_ascii=False, indent=2)


def _parse_args() -> argparse.Namespace:
    """يبني محلل المعاملات لسطر الأوامر من أجل تشغيل الأداة بسهولة."""

    parser = argparse.ArgumentParser(description="عرض خريطة بنية المشروع بصيغة JSON")
    parser.add_argument("root", nargs="?", default=Path.cwd(), type=Path, help="مسار الجذر المراد مسحه")
    parser.add_argument("--include-hidden", action="store_true", help="إظهار الملفات والمجلدات المخفية")
    parser.add_argument("--max-depth", type=int, default=None, help="أقصى عمق للغوص داخل البنية")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(emit_repository_map(args.root, include_hidden=args.include_hidden, max_depth=args.max_depth))
