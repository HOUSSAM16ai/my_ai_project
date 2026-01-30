from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """
    تصنيف أنواع العقد في الرسم البياني المعرفي.
    """
    ENTITY = "entity"       # كيان مادي (مثال: صندوق، كرة)
    EVENT = "event"         # حدث (مثال: سحب كرة)
    CONCEPT = "concept"     # مفهوم رياضي (مثال: الاحتمال)
    RULE = "rule"           # قاعدة منطقية (مثال: قانون المجموع)
    VALUE = "value"         # قيمة عددية


class RelationType(str, Enum):
    """
    تصنيف أنواع العلاقات بين العقد.
    """
    CONTAINS = "contains"       # يحتوي (الصندوق يحتوي كرات)
    REQUIRES = "requires"       # يتطلب (الحدث يتطلب قانون)
    DEFINES = "defines"         # يعرف (القاعدة تعرف القيمة)
    CALCULATED_BY = "calculated_by" # يحسب بواسطة
    VERIFIES = "verifies"       # يؤكد صحة


class KnowledgeNode(BaseModel):
    """
    يمثل عقدة معرفية واحدة في الرسم البياني.
    تحتوي هذه العقدة على البيانات الأساسية والخصائص الديناميكية.
    """
    id: str = Field(..., description="المعرف الفريد للعقدة")
    type: NodeType = Field(..., description="نوع العقدة")
    label: str = Field(..., description="تسمية العقدة للعرض")
    attributes: dict[str, Any] = Field(default_factory=dict, description="الخصائص الديناميكية للعقدة")

    def __hash__(self) -> int:
        return hash(self.id)


class Relation(BaseModel):
    """
    تمثل علاقة موجهة بين عقدتين في الرسم البياني.
    """
    source_id: str = Field(..., description="معرف عقدة المصدر")
    target_id: str = Field(..., description="معرف عقدة الهدف")
    type: RelationType = Field(..., description="نوع العلاقة")
    metadata: dict[str, Any] = Field(default_factory=dict, description="بيانات وصفية للعلاقة")


class AuditStatus(str, Enum):
    """
    حالة نتيجة التدقيق الإجرائي.
    """
    PASS = "pass"       # نجاح التدقيق
    FAIL = "fail"       # فشل التدقيق (وجود احتيال أو خطأ منطقي)
    WARNING = "warning" # تحذير (قيمة غير اعتيادية)


class AuditResult(BaseModel):
    """
    نتيجة عملية التدقيق أو الفحص المنطقي.
    يستخدم هذا النموذج لتقديم تقرير نهائي عن صحة الإجراءات.
    """
    rule_id: str = Field(..., description="معرف القاعدة التي تم فحصها")
    status: AuditStatus = Field(..., description="حالة النتيجة")
    message: str = Field(..., description="رسالة توضيحية باللغة العربية")
    evidence: list[str] = Field(default_factory=list, description="الأدلة أو العقد التي سببت النتيجة")
    timestamp: float | None = Field(None, description="وقت التنفيذ")


class LogicRuleProtocol(Protocol):
    """
    بروتوكول للقواعد المنطقية التي تقوم بفحص الرسم البياني.
    يجب على كل قاعدة أن تنفذ هذا التوقيع.
    """
    def __call__(self, nodes: list[KnowledgeNode], relations: list[Relation]) -> AuditResult:
        ...


class ProceduralGraph(BaseModel):
    """
    يمثل الرسم البياني الكامل الذي يحتوي على كافة العقد والعلاقات.
    """
    nodes: dict[str, KnowledgeNode] = Field(default_factory=dict)
    relations: list[Relation] = Field(default_factory=list)

    def add_node(self, node: KnowledgeNode) -> None:
        """إضافة عقدة جديدة للرسم البياني"""
        self.nodes[node.id] = node

    def add_relation(self, relation: Relation) -> None:
        """إضافة علاقة جديدة"""
        self.relations.append(relation)

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        """استرجاع عقدة بواسطة المعرف"""
        return self.nodes.get(node_id)
