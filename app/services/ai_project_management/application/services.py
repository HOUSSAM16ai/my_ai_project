"""
Application Services for AI Project Management
Contains business logic for scheduling, risk assessment, and predictions.
"""
import statistics
from collections import defaultdict
from typing import Any
from ..domain.models import Risk, RiskLevel, Task, TaskStatus, TeamMember


class PredictiveTaskAnalyzer:
    """
    محلل مهام تنبؤي يستخدم ML للتنبؤ بالمدة والمشاكل
    """

    def __init__(self):
        self.historical_tasks: list[Task] = []
        self.prediction_accuracy: dict[str, float] = defaultdict(lambda : 0.5)

    def predict_task_duration(self, task: Task, assignee: (TeamMember |
        None)=None) ->tuple[float, float]:
        """
        التنبؤ بمدة المهمة الفعلية
        Returns: (predicted_hours, confidence)
        """
        similar_tasks = self._find_similar_tasks(task)
        if not similar_tasks:
            return task.estimated_hours, 0.3
        ratios = []
        for hist_task in similar_tasks:
            if hist_task.estimated_hours > 0 and hist_task.actual_hours > 0:
                ratio = hist_task.actual_hours / hist_task.estimated_hours
                ratios.append(ratio)
        if not ratios:
            return task.estimated_hours, 0.3
        avg_ratio = statistics.mean(ratios)
        variance = statistics.variance(ratios) if len(ratios) > 1 else 1.0
        if assignee:
            avg_ratio /= assignee.performance_score
        predicted_hours = task.estimated_hours * avg_ratio
        confidence = min(0.95, 0.5 + len(ratios) / 20 - variance * 0.1)
        return predicted_hours, confidence

    def _find_similar_tasks(self, task: Task, limit: int=10) ->list[Task]:
        """إيجاد مهام مشابهة من التاريخ"""
        scored_tasks = []
        for hist_task in self.historical_tasks:
            if hist_task.status != TaskStatus.DONE:
                continue
            similarity = self._calculate_similarity(task, hist_task)
            scored_tasks.append((similarity, hist_task))
        scored_tasks.sort(reverse=True, key=lambda x: x[0])
        return [t for _, t in scored_tasks[:limit]]

    def _calculate_similarity(self, task1: Task, task2: Task) ->float:
        """حساب التشابه بين مهمتين"""
        score = 0.0
        if task1.priority == task2.priority:
            score += 0.3
        if task1.estimated_hours > 0 and task2.estimated_hours > 0:
            ratio = min(task1.estimated_hours, task2.estimated_hours) / max(
                task1.estimated_hours, task2.estimated_hours)
            score += ratio * 0.3
        common_tags = set(task1.tags) & set(task2.tags)
        if task1.tags and task2.tags:
            tag_similarity = len(common_tags) / max(len(task1.tags), len(
                task2.tags))
            score += tag_similarity * 0.4
        return score

    def identify_bottlenecks(self, tasks: list[Task]) ->list[dict[str, Any]]:
        """تحديد الاختناقات في المشروع"""
        bottlenecks = []
        for task in tasks:
            if len(task.dependencies) > 3:
                bottlenecks.append({'task_id': task.task_id, 'type':
                    'dependency_overload', 'severity': 'high',
                    'description':
                    f'Task has {len(task.dependencies)} dependencies'})
        blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED]
        if len(blocked_tasks) > len(tasks) * 0.2:
            bottlenecks.append({'type': 'high_block_rate', 'severity':
                'critical', 'description':
                f'{len(blocked_tasks)} tasks are blocked ({len(blocked_tasks) / len(tasks) * 100:.0f}%)'
                })
        overdue = [t for t in tasks if t.is_overdue()]
        if overdue:
            bottlenecks.append({'type': 'overdue_tasks', 'severity': 'high',
                'description': f'{len(overdue)} tasks are overdue'})
        return bottlenecks


class SmartScheduler:
    """
    جدولة ذكية تستخدم ML لتحسين الجدول الزمني
    """

    def __init__(self):
        self.task_analyzer = PredictiveTaskAnalyzer()

    def _topological_sort(self, tasks: list[Task]) ->list[Task]:
        """ترتيب طوبولوجي للمهام بناءً على التبعيات"""
        sorted_tasks = []
        no_deps = [t for t in tasks if not t.dependencies]
        with_deps = [t for t in tasks if t.dependencies]
        sorted_tasks.extend(sorted(no_deps, key=lambda t: t.priority.value,
            reverse=True))
        sorted_tasks.extend(sorted(with_deps, key=lambda t: t.priority.
            value, reverse=True))
        return sorted_tasks

    def _find_best_assignee(self, task: Task, team: list[TeamMember],
        current_assignments: dict[str, list[Task]]) ->(TeamMember | None):
        """إيجاد أفضل عضو فريق للمهمة"""
        scored_members = []
        for member in team:
            score = self._calculate_assignment_score(task, member,
                current_assignments[member.member_id])
            scored_members.append((score, member))
        scored_members.sort(reverse=True, key=lambda x: x[0])
        if scored_members:
            return scored_members[0][1]
        return None

    def _calculate_assignment_score(self, task: Task, member: TeamMember,
        current_tasks: list[Task]) ->float:
        """حساب درجة ملاءمة العضو للمهمة"""
        score = 0.0
        score += member.availability() * 40
        score += member.performance_score * 30
        task_tags_set = set(task.tags)
        member_skills_set = set(member.skills)
        if task_tags_set and member_skills_set:
            skills_match = len(task_tags_set & member_skills_set) / len(
                task_tags_set)
            score += skills_match * 30
        return score


class RiskAssessor:
    """
    مُقيم المخاطر الذكي
    """

    def __init__(self):
        self.risk_history: list[Risk] = []

    def assess_project_risks(self, tasks: list[Task], team: list[TeamMember]
        ) ->list[Risk]:
        """تقييم مخاطر المشروع"""
        risks = []
        for member in team:
            if (member.current_workload > member.capacity_hours_per_day * 5 *
                1.2):
                risks.append(Risk(risk_id=
                    f'risk_overload_{member.member_id}', title=
                    f'Team Member Overload: {member.name}', description=
                    f'{member.name} is overloaded with {member.current_workload:.1f} hours'
                    , level=RiskLevel.HIGH, probability=0.9, impact=7.0,
                    mitigation_plan='Redistribute tasks or extend timeline'))
        overdue = [t for t in tasks if t.is_overdue()]
        if len(overdue) > len(tasks) * 0.15:
            risks.append(Risk(risk_id='risk_overdue', title=
                'High Overdue Task Rate', description=
                f'{len(overdue)} tasks are overdue', level=RiskLevel.
                CRITICAL, probability=1.0, impact=9.0, mitigation_plan=
                'Review priorities and extend deadlines'))
        blocked = [t for t in tasks if t.status == TaskStatus.BLOCKED]
        if blocked:
            risks.append(Risk(risk_id='risk_blocked', title='Blocked Tasks',
                description=f'{len(blocked)} tasks are blocked', level=
                RiskLevel.HIGH, probability=0.8, impact=6.0,
                mitigation_plan='Resolve blockers immediately'))
        required_skills = set()
        for task in tasks:
            required_skills.update(task.tags)
        available_skills = set()
        for member in team:
            available_skills.update(member.skills)
        missing_skills = required_skills - available_skills
        if missing_skills:
            risks.append(Risk(risk_id='risk_skills', title='Missing Skills',
                description=
                f"Skills needed but not in team: {', '.join(missing_skills)}",
                level=RiskLevel.MEDIUM, probability=0.7, impact=5.0,
                mitigation_plan='Train team or hire contractors'))
        return sorted(risks, key=lambda r: r.risk_score(), reverse=True)


class ProjectOrchestrator:
    """
    المُنسق الرئيسي للمشروع - يجمع كل الأنظمة الذكية
    """

    def __init__(self):
        self.task_analyzer = PredictiveTaskAnalyzer()
        self.scheduler = SmartScheduler()
        self.risk_assessor = RiskAssessor()
        self.tasks: list[Task] = []
        self.team: list[TeamMember] = []

    def _generate_recommendations(self, risks: list[Risk], bottlenecks:
        list[dict], completion_rate: float) ->list[str]:
        """توليد توصيات ذكية"""
        recommendations = []
        if completion_rate < 0.3:
            recommendations.append(
                '🚀 Project is in early stages. Focus on establishing clear goals and priorities.'
                )
        if risks:
            top_risk = risks[0]
            recommendations.append(
                f'⚠️ Top risk: {top_risk.title}. {top_risk.mitigation_plan}')
        if bottlenecks:
            recommendations.append(
                f'🔧 {len(bottlenecks)} bottlenecks detected. Review and resolve blockers.'
                )
        if not recommendations:
            recommendations.append(
                '✅ Project is on track. Continue current pace.')
        return recommendations
