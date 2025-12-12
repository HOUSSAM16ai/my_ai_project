"""
Domain Models for AI Project Management
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskPriority(Enum):
    """أولوية المهمة"""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1


class TaskStatus(Enum):
    """حالة المهمة"""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """مستوى المخاطر"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class Task:
    """مهمة في المشروع"""

    task_id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    estimated_hours: float
    actual_hours: float = 0.0
    assignee: str | None = None
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline: datetime | None = None
    tags: list[str] = field(default_factory=list)

    def is_overdue(self) -> bool:
        """هل المهمة متأخرة؟"""
        if not self.deadline or self.status == TaskStatus.DONE:
            return False
        return datetime.now() > self.deadline

    def completion_percentage(self) -> float:
        """نسبة الإنجاز"""
        if self.status == TaskStatus.DONE:
            return 100.0
        if self.status == TaskStatus.BACKLOG:
            return 0.0
        if self.status == TaskStatus.IN_PROGRESS and self.estimated_hours > 0:
            return min(100, (self.actual_hours / self.estimated_hours) * 100)
        return 0.0


@dataclass
class Risk:
    """مخاطر المشروع"""

    risk_id: str
    title: str
    description: str
    level: RiskLevel
    probability: float  # 0-1
    impact: float  # 0-10
    mitigation_plan: str
    owner: str | None = None
    identified_at: datetime = field(default_factory=datetime.now)

    def risk_score(self) -> float:
        """حساب درجة المخاطر"""
        return self.probability * self.impact


@dataclass
class TeamMember:
    """عضو الفريق"""

    member_id: str
    name: str
    role: str
    capacity_hours_per_day: float = 8.0
    skills: list[str] = field(default_factory=list)
    current_workload: float = 0.0  # hours
    performance_score: float = 1.0  # multiplier

    def availability(self) -> float:
        """التوفر (0-1)"""
        max_capacity = self.capacity_hours_per_day * 5  # per week
        return max(0, 1 - (self.current_workload / max_capacity))
