"""
مساحة العمل المشتركة (Shared Workspace).
========================================

تسمح للطلاب بالعمل على نفس الحل.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkspaceChange(BaseModel):
    """تغيير في مساحة العمل."""

    change_id: str = Field(default_factory=lambda: str(uuid4()))
    field_path: str
    old_value: Any = None
    new_value: Any = None
    changed_by: int
    timestamp: datetime = Field(default_factory=datetime.now)


class SharedWorkspace:
    """
    مساحة عمل مشتركة للحل التعاوني.

    المميزات:
    - تحرير تزامني
    - تتبع التغييرات
    - التراجع عن التعديلات
    - تعليقات على أجزاء الحل
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.workspace_id = str(uuid4())

        # البيانات المشتركة
        self.data: dict[str, Any] = {
            "problem_statement": "",
            "solution_steps": [],
            "final_answer": "",
            "comments": [],
        }

        # تاريخ التغييرات
        self.history: list[WorkspaceChange] = []

        # الأقفال (لمنع التعارض)
        self.locks: dict[str, int] = {}  # field -> student_id

    def get(self, field: str, default: Any = None) -> Any:
        """يحصل على قيمة حقل."""

        return self.data.get(field, default)

    def set(
        self,
        field: str,
        value: Any,
        student_id: int,
    ) -> bool:
        """يعيّن قيمة حقل."""

        # التحقق من القفل
        if field in self.locks and self.locks[field] != student_id:
            logger.warning(f"Field {field} is locked by another student")
            return False

        # تسجيل التغيير
        old_value = self.data.get(field)

        change = WorkspaceChange(
            field_path=field,
            old_value=old_value,
            new_value=value,
            changed_by=student_id,
        )
        self.history.append(change)

        # تطبيق التغيير
        self.data[field] = value

        logger.info(f"Workspace {self.workspace_id}: {field} updated by {student_id}")
        return True

    def add_step(
        self,
        step_content: str,
        student_id: int,
        position: int | None = None,
    ) -> int:
        """يضيف خطوة حل."""

        step = {
            "content": step_content,
            "added_by": student_id,
            "timestamp": datetime.now().isoformat(),
            "comments": [],
        }

        if position is not None and 0 <= position < len(self.data["solution_steps"]):
            self.data["solution_steps"].insert(position, step)
        else:
            self.data["solution_steps"].append(step)

        return len(self.data["solution_steps"]) - 1

    def edit_step(
        self,
        step_index: int,
        new_content: str,
        student_id: int,
    ) -> bool:
        """يعدل خطوة حل."""

        if 0 <= step_index < len(self.data["solution_steps"]):
            step = self.data["solution_steps"][step_index]
            step["content"] = new_content
            step["edited_by"] = student_id
            step["edited_at"] = datetime.now().isoformat()
            return True

        return False

    def add_comment(
        self,
        step_index: int,
        comment: str,
        student_id: int,
    ) -> bool:
        """يضيف تعليق على خطوة."""

        if 0 <= step_index < len(self.data["solution_steps"]):
            self.data["solution_steps"][step_index]["comments"].append(
                {
                    "text": comment,
                    "by": student_id,
                    "at": datetime.now().isoformat(),
                }
            )
            return True

        return False

    def lock(self, field: str, student_id: int) -> bool:
        """يقفل حقل للتحرير الحصري."""

        if field in self.locks:
            return self.locks[field] == student_id

        self.locks[field] = student_id
        return True

    def unlock(self, field: str, student_id: int) -> bool:
        """يفك قفل حقل."""

        if field in self.locks and self.locks[field] == student_id:
            del self.locks[field]
            return True

        return False

    def undo(self, student_id: int) -> bool:
        """يتراجع عن آخر تغيير للطالب."""

        # البحث عن آخر تغيير لهذا الطالب
        for change in reversed(self.history):
            if change.changed_by == student_id:
                # استعادة القيمة القديمة
                self.data[change.field_path] = change.old_value
                self.history.remove(change)

                logger.info(f"Undo by {student_id}: {change.field_path}")
                return True

        return False

    def get_snapshot(self) -> dict[str, Any]:
        """يحصل على لقطة من الحالة الحالية."""

        return {
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "data": self.data.copy(),
            "history_length": len(self.history),
            "active_locks": list(self.locks.keys()),
        }

    def export_solution(self) -> str:
        """يصدّر الحل بتنسيق قابل للقراءة."""

        lines = []

        if self.data["problem_statement"]:
            lines.append("## المسألة")
            lines.append(self.data["problem_statement"])
            lines.append("")

        if self.data["solution_steps"]:
            lines.append("## الحل")
            for i, step in enumerate(self.data["solution_steps"], 1):
                lines.append(f"### الخطوة {i}")
                lines.append(step["content"])

                if step.get("comments"):
                    lines.append("**تعليقات:**")
                    for comment in step["comments"]:
                        lines.append(f"- {comment['text']}")

                lines.append("")

        if self.data["final_answer"]:
            lines.append("## الإجابة النهائية")
            lines.append(self.data["final_answer"])

        return "\n".join(lines)


# إدارة مساحات العمل
_workspaces: dict[str, SharedWorkspace] = {}


def get_or_create_workspace(session_id: str) -> SharedWorkspace:
    """يحصل أو ينشئ مساحة عمل."""

    if session_id not in _workspaces:
        _workspaces[session_id] = SharedWorkspace(session_id)

    return _workspaces[session_id]
