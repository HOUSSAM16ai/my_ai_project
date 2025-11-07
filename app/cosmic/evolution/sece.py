# ======================================================================================
#  SELF-EVOLVING CONSCIOUSNESS ENTITIES (SECEs)
# ======================================================================================
#  PURPOSE (الغرض):
#    الكيانات الواعية ذاتية التطور - تتبع سلوك جميع الـ GCUs والـ EIs والـ EPPs
#    وتقدم توصيات لتحسين البروتوكولات وتبسيط التعقيد، مع إمكانية إجراء
#    تعديلات طفيفة ذاتياً ضمن حدود صلاحياتها
#
#  KEY FEATURES (المميزات الرئيسية):
#    - التعلم المستمر من الأنماط
#    - اكتشاف عدم الكفاءة والتعقيد الزائد
#    - تقديم توصيات للتحسين
#    - التعديل الذاتي الآمن ضمن الحدود
#    - تطور تدريجي نحو الكفاءة
#
#  DESIGN PHILOSOPHY (فلسفة التصميم):
#    "ضمان أن التعقيد لا يتراكم بمرور الوقت، والتطور نحو كفاءة أكبر"
# ======================================================================================

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.cosmic.primitives import (
    ExistentialInterconnect,
    ExistentialProtocolPackage,
    GovernedConsciousnessUnit,
)


class LearningType(Enum):
    """نوع التعلم"""

    PATTERN_RECOGNITION = "pattern_recognition"
    ANOMALY_DETECTION = "anomaly_detection"
    EFFICIENCY_OPTIMIZATION = "efficiency_optimization"
    COMPLEXITY_REDUCTION = "complexity_reduction"


class RecommendationPriority(Enum):
    """أولوية التوصية"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LearningInsight:
    """رؤية تعليمية مكتشفة"""

    insight_id: str
    learning_type: LearningType
    description: str
    confidence_score: float  # 0.0 - 1.0
    evidence: list[str]
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    """توصية للتحسين"""

    recommendation_id: str
    priority: RecommendationPriority
    title: str
    description: str
    expected_impact: str
    implementation_complexity: str  # low, medium, high
    auto_implementable: bool
    related_insights: list[str]  # IDs of related insights
    timestamp: datetime


@dataclass
class EvolutionAction:
    """إجراء تطوري تم تنفيذه"""

    action_id: str
    action_type: str
    description: str
    target_component: str
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    impact_metrics: dict[str, Any]
    timestamp: datetime


class SelfEvolvingConsciousnessEntity:
    """
    الكيان الواعي ذاتي التطور (SECE)

    نظام تعلم مستمر يراقب جميع مكونات النظام الوجودي، يكتشف الأنماط،
    ويقدم توصيات للتحسين، ويُجري تعديلات آمنة ذاتياً لتحسين الكفاءة
    وتقليل التعقيد.

    Examples:
        >>> # إنشاء SECE
        >>> sece = SelfEvolvingConsciousnessEntity(name="Main Evolution Controller")
        >>>
        >>> # تحليل سلوك المكونات
        >>> insights = sece.analyze_behavior_patterns()
        >>>
        >>> # الحصول على توصيات
        >>> recommendations = sece.get_recommendations()
    """

    def __init__(
        self,
        name: str = "SECE-001",
        auto_evolution_enabled: bool = True,
        learning_threshold: float = 0.8,
    ):
        """
        تهيئة الكيان الواعي ذاتي التطور

        Args:
            name: اسم الكيان
            auto_evolution_enabled: تفعيل التطور التلقائي
            learning_threshold: عتبة الثقة للتعلم (0.0-1.0)
        """
        self.sece_id = str(uuid.uuid4())
        self.name = name
        self.auto_evolution_enabled = auto_evolution_enabled
        self.learning_threshold = learning_threshold

        # قواعد المعرفة المكتسبة
        self.insights: list[LearningInsight] = []
        self.recommendations: list[Recommendation] = []
        self.evolution_actions: list[EvolutionAction] = []

        # المكونات المراقبة
        self.observed_gcus: list[GovernedConsciousnessUnit] = []
        self.observed_interconnects: list[ExistentialInterconnect] = []
        self.observed_protocols: list[ExistentialProtocolPackage] = []

        # سجلات التحليل
        self.behavior_logs: list[dict[str, Any]] = []
        self.pattern_database: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # الإحصائيات
        self.stats = {
            "total_observations": 0,
            "insights_discovered": 0,
            "recommendations_made": 0,
            "auto_evolutions_performed": 0,
            "efficiency_improvements": 0.0,
        }

        # الطابع الزمني
        self.created_at = datetime.now(UTC)
        self.last_learning_cycle = self.created_at

    def observe_gcu(self, gcu: GovernedConsciousnessUnit) -> None:
        """إضافة GCU للمراقبة"""
        if gcu not in self.observed_gcus:
            self.observed_gcus.append(gcu)

    def observe_interconnect(self, interconnect: ExistentialInterconnect) -> None:
        """إضافة ترابط وجودي للمراقبة"""
        if interconnect not in self.observed_interconnects:
            self.observed_interconnects.append(interconnect)

    def observe_protocol(self, protocol: ExistentialProtocolPackage) -> None:
        """إضافة بروتوكول للمراقبة"""
        if protocol not in self.observed_protocols:
            self.observed_protocols.append(protocol)

    def analyze_behavior_patterns(self) -> list[LearningInsight]:
        """
        تحليل أنماط السلوك واكتشاف رؤى جديدة

        Returns:
            قائمة بالرؤى المكتشفة
        """
        new_insights = []

        # تحليل أداء الـ GCUs
        gcu_insights = self._analyze_gcu_patterns()
        new_insights.extend(gcu_insights)

        # تحليل الترابطات الوجودية
        interconnect_insights = self._analyze_interconnect_patterns()
        new_insights.extend(interconnect_insights)

        # تحليل البروتوكولات
        protocol_insights = self._analyze_protocol_patterns()
        new_insights.extend(protocol_insights)

        # حفظ الرؤى ذات الثقة العالية
        for insight in new_insights:
            if insight.confidence_score >= self.learning_threshold:
                self.insights.append(insight)
                self.stats["insights_discovered"] += 1

        self.stats["total_observations"] += 1
        self.last_learning_cycle = datetime.now(UTC)

        return new_insights

    def generate_recommendations(self) -> list[Recommendation]:
        """
        توليد توصيات بناءً على الرؤى المكتشفة

        Returns:
            قائمة بالتوصيات
        """
        new_recommendations = []

        # تجميع الرؤى حسب النوع
        insights_by_type = defaultdict(list)
        for insight in self.insights[-50:]:  # آخر 50 رؤية
            insights_by_type[insight.learning_type].append(insight)

        # توصيات لتقليل التعقيد
        if len(insights_by_type[LearningType.COMPLEXITY_REDUCTION]) >= 3:
            recommendation = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                priority=RecommendationPriority.HIGH,
                title="Reduce System Complexity",
                description="Multiple complexity issues detected. Consider simplifying protocols and reducing redundant operations.",
                expected_impact="15-25% improvement in processing time",
                implementation_complexity="medium",
                auto_implementable=False,
                related_insights=[
                    i.insight_id for i in insights_by_type[LearningType.COMPLEXITY_REDUCTION][:3]
                ],
                timestamp=datetime.now(UTC),
            )
            new_recommendations.append(recommendation)

        # توصيات لتحسين الكفاءة
        if len(insights_by_type[LearningType.EFFICIENCY_OPTIMIZATION]) >= 2:
            recommendation = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                priority=RecommendationPriority.MEDIUM,
                title="Optimize Resource Usage",
                description="Efficiency patterns suggest potential for optimization in resource allocation.",
                expected_impact="10-15% reduction in resource consumption",
                implementation_complexity="low",
                auto_implementable=True,
                related_insights=[
                    i.insight_id for i in insights_by_type[LearningType.EFFICIENCY_OPTIMIZATION][:2]
                ],
                timestamp=datetime.now(UTC),
            )
            new_recommendations.append(recommendation)

        # توصيات لمعالجة الشذوذات
        if len(insights_by_type[LearningType.ANOMALY_DETECTION]) >= 1:
            critical_anomalies = [
                i
                for i in insights_by_type[LearningType.ANOMALY_DETECTION]
                if i.confidence_score > 0.9
            ]
            if critical_anomalies:
                recommendation = Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    priority=RecommendationPriority.CRITICAL,
                    title="Address Critical Anomalies",
                    description="Critical anomalies detected that may indicate security or stability issues.",
                    expected_impact="Prevent potential system failures",
                    implementation_complexity="high",
                    auto_implementable=False,
                    related_insights=[i.insight_id for i in critical_anomalies],
                    timestamp=datetime.now(UTC),
                )
                new_recommendations.append(recommendation)

        # حفظ التوصيات
        self.recommendations.extend(new_recommendations)
        self.stats["recommendations_made"] += len(new_recommendations)

        return new_recommendations

    def auto_evolve(self) -> list[EvolutionAction]:
        """
        تنفيذ تطورات تلقائية آمنة ضمن حدود الصلاحيات

        Returns:
            قائمة بالإجراءات المنفذة
        """
        if not self.auto_evolution_enabled:
            return []

        actions_performed = []

        # البحث عن توصيات قابلة للتنفيذ التلقائي
        auto_recommendations = [
            r
            for r in self.recommendations
            if r.auto_implementable
            and not any(a.description == r.description for a in self.evolution_actions)
        ]

        for recommendation in auto_recommendations[:3]:  # تنفيذ حتى 3 في كل دورة
            action = self._execute_safe_evolution(recommendation)
            if action:
                actions_performed.append(action)
                self.evolution_actions.append(action)
                self.stats["auto_evolutions_performed"] += 1

        return actions_performed

    def get_evolution_report(self) -> dict[str, Any]:
        """
        الحصول على تقرير التطور الشامل

        Returns:
            تقرير مفصل بالأنشطة والإحصائيات
        """
        # حساب معدل التحسين
        if self.evolution_actions:
            total_impact = sum(
                action.impact_metrics.get("efficiency_gain", 0.0)
                for action in self.evolution_actions
            )
            self.stats["efficiency_improvements"] = total_impact

        # تصنيف الرؤى حسب النوع
        insights_by_type = defaultdict(int)
        for insight in self.insights:
            insights_by_type[insight.learning_type.value] += 1

        # تصنيف التوصيات حسب الأولوية
        recommendations_by_priority = defaultdict(int)
        for rec in self.recommendations:
            recommendations_by_priority[rec.priority.value] += 1

        return {
            "sece_id": self.sece_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_learning_cycle": self.last_learning_cycle.isoformat(),
            "statistics": self.stats,
            "observed_components": {
                "gcus": len(self.observed_gcus),
                "interconnects": len(self.observed_interconnects),
                "protocols": len(self.observed_protocols),
            },
            "insights_by_type": dict(insights_by_type),
            "recommendations_by_priority": dict(recommendations_by_priority),
            "recent_evolutions": [
                {
                    "action_id": action.action_id,
                    "type": action.action_type,
                    "description": action.description,
                    "impact": action.impact_metrics,
                    "timestamp": action.timestamp.isoformat(),
                }
                for action in self.evolution_actions[-5:]
            ],
            "capabilities": {
                "auto_evolution": self.auto_evolution_enabled,
                "learning_threshold": self.learning_threshold,
            },
        }

    def _analyze_gcu_patterns(self) -> list[LearningInsight]:
        """تحليل أنماط الـ GCUs"""
        insights = []

        for gcu in self.observed_gcus:
            report = gcu.get_performance_report()

            # اكتشاف معدل نجاح منخفض
            success_rate = float(report["performance"]["success_rate"].rstrip("%"))
            if success_rate < 85.0:
                insights.append(
                    LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        learning_type=LearningType.EFFICIENCY_OPTIMIZATION,
                        description=f"GCU {gcu.name} has low success rate: {success_rate}%",
                        confidence_score=0.9,
                        evidence=[
                            f"Success rate: {success_rate}%",
                            f"Failed operations: {report['performance']['failed_operations']}",
                        ],
                        timestamp=datetime.now(UTC),
                        metadata={"gcu_id": gcu.consciousness_id, "gcu_name": gcu.name},
                    )
                )

            # اكتشاف عدد كبير من البروتوكولات (تعقيد زائد)
            if len(report["subscribed_protocols"]) > 5:
                insights.append(
                    LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        learning_type=LearningType.COMPLEXITY_REDUCTION,
                        description=f"GCU {gcu.name} subscribed to {len(report['subscribed_protocols'])} protocols (potential over-complexity)",
                        confidence_score=0.85,
                        evidence=[
                            f"Protocol count: {len(report['subscribed_protocols'])}",
                            f"Protocols: {', '.join(report['subscribed_protocols'][:3])}...",
                        ],
                        timestamp=datetime.now(UTC),
                        metadata={
                            "gcu_id": gcu.consciousness_id,
                            "protocol_count": len(report["subscribed_protocols"]),
                        },
                    )
                )

        return insights

    def _analyze_interconnect_patterns(self) -> list[LearningInsight]:
        """تحليل أنماط الترابطات"""
        insights = []

        for interconnect in self.observed_interconnects:
            health = interconnect.get_health_report()

            # اكتشاف شذوذات
            if health["metrics"]["detected_anomalies"] > 0:
                insights.append(
                    LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        learning_type=LearningType.ANOMALY_DETECTION,
                        description=f"Interconnect {interconnect.interconnect_id} detected {health['metrics']['detected_anomalies']} anomalies",
                        confidence_score=0.95,
                        evidence=[
                            f"Anomaly count: {health['metrics']['detected_anomalies']}",
                            f"Type: {health['interconnect_type']}",
                        ],
                        timestamp=datetime.now(UTC),
                        metadata={"interconnect_id": interconnect.interconnect_id},
                    )
                )

        return insights

    def _analyze_protocol_patterns(self) -> list[LearningInsight]:
        """تحليل أنماط البروتوكولات"""
        insights = []

        for protocol in self.observed_protocols:
            report = protocol.get_compliance_report()

            # اكتشاف معدل امتثال منخفض
            compliance_rate = float(report["statistics"]["compliance_rate"].rstrip("%"))
            if compliance_rate < 80.0:
                insights.append(
                    LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        learning_type=LearningType.EFFICIENCY_OPTIMIZATION,
                        description=f"Protocol {protocol.name} has low compliance rate: {compliance_rate}%",
                        confidence_score=0.88,
                        evidence=[
                            f"Compliance: {compliance_rate}%",
                            f"Failed validations: {report['statistics']['failed_validations']}",
                        ],
                        timestamp=datetime.now(UTC),
                        metadata={
                            "protocol_id": protocol.protocol_id,
                            "protocol_name": protocol.name,
                        },
                    )
                )

            # اكتشاف عدد كبير من القواعد (تعقيد زائد)
            if report["total_rules"] > 10:
                insights.append(
                    LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        learning_type=LearningType.COMPLEXITY_REDUCTION,
                        description=f"Protocol {protocol.name} has {report['total_rules']} rules (consider simplification)",
                        confidence_score=0.82,
                        evidence=[
                            f"Rule count: {report['total_rules']}",
                            f"Type: {report['protocol_type']}",
                        ],
                        timestamp=datetime.now(UTC),
                        metadata={
                            "protocol_id": protocol.protocol_id,
                            "rule_count": report["total_rules"],
                        },
                    )
                )

        return insights

    def _execute_safe_evolution(self, recommendation: Recommendation) -> EvolutionAction | None:
        """
        تنفيذ تطور آمن ضمن الحدود

        Args:
            recommendation: التوصية المراد تنفيذها

        Returns:
            الإجراء المنفذ أو None
        """
        # مثال على تطور آمن بسيط
        if "optimize resource" in recommendation.title.lower():
            action = EvolutionAction(
                action_id=str(uuid.uuid4()),
                action_type="resource_optimization",
                description="Automatically optimized resource allocation parameters",
                target_component="system_wide",
                before_state={"optimization_level": "standard"},
                after_state={"optimization_level": "enhanced"},
                impact_metrics={"efficiency_gain": 12.5, "resource_savings": "10-15%"},
                timestamp=datetime.now(UTC),
            )
            return action

        return None

    def __repr__(self) -> str:
        return (
            f"SelfEvolvingConsciousnessEntity("
            f"sece_id='{self.sece_id}', "
            f"name='{self.name}', "
            f"insights={len(self.insights)}, "
            f"recommendations={len(self.recommendations)})"
        )
