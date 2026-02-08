"""
نماذج مواصفات نسيج الوكلاء المتعددين (MAF-1.0).
------------------------------------------------
يحدد هذا الملف البنى المعيارية لنظام الوكلاء عالي الاعتمادية
وفق عقيدة "المخرجات المبنية على الدليل".
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class AuditStatus(StrEnum):
    """
    حالات عملية التحقق أو التدقيق.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class MAFPhase(StrEnum):
    """
    المراحل المميزة لبروتوكول MAF.
    """

    GENERATE = "GENERATE"  # Production of Claims/Proposals
    ATTACK = "ATTACK"  # Adversarial testing / Critique
    VERIFY = "VERIFY"  # Formal verification against evidence
    SEAL = "SEAL"  # Finalization and Audit Bundling


class Evidence(BaseModel):
    """
    دليل يمكن التحقق منه يدعم الادعاء.
    """

    id: str = Field(..., description="Unique identifier for the evidence")
    content: str = Field(..., description="The evidence content (quote, result, axiom)")
    source_type: str = Field(..., description="Type: 'document', 'simulation', 'logic', 'axiom'")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    metadata: dict[str, object] = Field(default_factory=dict)


class Claim(BaseModel):
    """
    نتيجة جزئية أو ادعاء يتطلب أدلة داعمة.
    """

    id: str = Field(..., description="Unique identifier for the claim")
    content: str = Field(..., description="The assertion text")
    evidence_ids: list[str] = Field(default_factory=list, description="IDs of supporting evidence")


class Proposal(BaseModel):
    """
    مقترح الوكيل الذي يحتوي على الادعاءات والتقديرات.
    """

    claims: list[Claim] = Field(default_factory=list)
    cost_est: float = Field(0.0, description="Estimated computational cost")
    risk_est: float = Field(0.0, description="Estimated risk score")
    time_est: float = Field(0.0, description="Estimated latency")
    raw_content: str = Field(..., description="The original text content of the proposal")


class AttackReport(BaseModel):
    """
    نتيجة هجوم خصمي على المقترح.
    """

    counterexamples: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    severity: float = Field(0.0, description="Severity of the attack 0.0-10.0")
    successful: bool = Field(..., description="True if the attack found significant flaws")
    feedback: str = Field(..., description="Constructive feedback for regeneration")


class ReviewChecklist(BaseModel):
    """
    قائمة الفحص العملية لدورة المنتج-المراجع.
    """

    requirements_met: bool = Field(..., description="Did it meet all stated requirements?")
    constraints_met: bool = Field(
        ..., description="Did it adhere to time/resource/policy constraints?"
    )
    assumptions_flagged: list[str] = Field(
        default_factory=list, description="List of unauthorized assumptions found"
    )
    contradictions_found: list[str] = Field(
        default_factory=list, description="List of internal contradictions or logic gaps"
    )
    justification_clear: bool = Field(
        ..., description="Is there a clear cause/reason for every claim?"
    )
    worst_case_analysis: str = Field(..., description="What is the worst-case failure mode?")
    minimal_fix_suggestion: str = Field(..., description="The smallest edit to achieve quality.")


class ReviewPacket(BaseModel):
    """
    حزمة المراجعة (خزمة مراجعة) للتغذية الراجعة التشغيلية.
    """

    checklist: ReviewChecklist
    score: float = Field(..., description="Quality score 0.0-10.0")
    actionable_feedback: str = Field(..., description="Specific instructions for the Maker")
    recommendation: str = Field(..., description="'APPROVE' or 'REJECT'")


class Verification(BaseModel):
    """
    نتيجة عملية التحقق الرسمية.
    """

    passed: bool = Field(..., description="True if all Critical Gates passed")
    status: AuditStatus = Field(default=AuditStatus.SKIPPED)
    evidence_ids: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    risk_score: float = Field(0.0, description="Residual risk score")


class AuditBundle(BaseModel):
    """
    المخرجات النهائية المختومة التي تحتوي على سلسلة المصدر كاملة.
    """

    task_id: str
    claims: list[Claim]
    evidence: list[Evidence]
    verification: Verification
    attack_report: AttackReport | None = None
    review_packet: ReviewPacket | None = None
    decision_reason: str
    final_text: str
