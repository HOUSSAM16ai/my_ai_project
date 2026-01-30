from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """
    تصنيف أنواع العقد في الرسم البياني المعرفي (Procedural & Fraud Detection).
    """

    # Generic Math/Logic Types
    ENTITY = "entity"
    EVENT = "event"
    CONCEPT = "concept"
    RULE = "rule"
    VALUE = "value"

    # Procurement & Fraud Types (The Agent as a Unit of Work)
    SUPPLIER = "supplier"  # مورد
    TENDER = "tender"  # مناقصة
    CONTRACT = "contract"  # عقد
    INVOICE = "invoice"  # فاتورة
    OFFICIAL = "official"  # مسؤول حكومي
    COMPANY = "company"  # شركة
    ADDRESS = "address"  # عنوان فعلي
    BANK_ACCOUNT = "bank_account"  # حساب بنكي


class RelationType(str, Enum):
    """
    تصنيف أنواع العلاقات بين العقد.
    """

    # Generic
    CONTAINS = "contains"
    REQUIRES = "requires"
    DEFINES = "defines"
    CALCULATED_BY = "calculated_by"
    VERIFIES = "verifies"

    # Procurement & Fraud Relations
    OWNS = "owns"  # يملك (شركة -> حساب)
    PARTICIPATED_IN = "participated_in"  # شارك في (مورد -> مناقصة)
    WON = "won"  # فاز بـ (مورد -> مناقصة)
    ISSUED_BY = "issued_by"  # صدرت عن (مناقصة -> هيئة)
    LOCATED_AT = "located_at"  # يقع في (شركة -> عنوان)
    RELATED_TO = "related_to"  # قرابة/علاقة (مسؤول -> مورد)
    TRANSFERRED_TO = "transferred_to"  # تحويل مالي (حساب -> حساب)
    SIGNED_BY = "signed_by"  # وقع بواسطة (عقد -> مسؤول)


class KnowledgeNode(BaseModel):
    """
    يمثل عقدة معرفية واحدة في الرسم البياني.
    """

    id: str = Field(..., description="المعرف الفريد للعقدة")
    type: NodeType = Field(..., description="نوع العقدة")
    label: str = Field(..., description="تسمية العقدة للعرض")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="الخصائص الديناميكية للعقدة"
    )

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

    PASS = "pass"  # نجاح التدقيق
    FAIL = "fail"  # فشل التدقيق (وجود احتيال أو خطأ منطقي)
    WARNING = "warning"  # تحذير (قيمة غير اعتيادية)


class AuditResult(BaseModel):
    """
    نتيجة عملية التدقيق لقاعدة واحدة.
    """

    rule_id: str = Field(..., description="معرف القاعدة التي تم فحصها")
    status: AuditStatus = Field(..., description="حالة النتيجة")
    message: str = Field(..., description="رسالة توضيحية باللغة العربية")
    evidence: list[str] = Field(
        default_factory=list, description="الأدلة أو معرفات العقد التي سببت النتيجة"
    )
    timestamp: float | None = Field(None, description="وقت التنفيذ")


class ComplianceReport(BaseModel):
    """
    عقد الامتثال والتقرير النهائي (The Compliance Contract).
    يمثل وثيقة رسمية تصدر عن الوكيل "المدقق".
    """

    audit_id: str = Field(..., description="معرف فريد لعملية التدقيق")
    target_entity: str = Field(..., description="الكيان أو العملية المستهدفة بالتدقيق")
    overall_status: AuditStatus = Field(..., description="الحالة العامة للامتثال")
    risk_score: float = Field(..., description="درجة المخاطرة من 0.0 (آمن) إلى 100.0 (خطر)")
    findings: list[AuditResult] = Field(..., description="قائمة النتائج التفصيلية")
    recommendations: list[str] = Field(default_factory=list, description="توصيات الوكيل")
    timestamp: float = Field(..., description="وقت إصدار التقرير")


class LogicRuleProtocol(Protocol):
    """
    بروتوكول للقواعد المنطقية التي تقوم بفحص الرسم البياني.
    """

    def __call__(self, nodes: list[KnowledgeNode], relations: list[Relation]) -> AuditResult: ...


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
