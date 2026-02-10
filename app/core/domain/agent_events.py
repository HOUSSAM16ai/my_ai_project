"""
عقد الأحداث الموحد للوكلاء (Unified Agent Event Contract).

يوفر هذا الملف تعريفات صارمة (Schema) للأحداث التي يرسلها النظام متعدد الوكلاء.
الهدف هو منع "انحراف العقد" (Contract Drift) بين المحرك (Backend) والواجهة (Frontend).
"""

from enum import StrEnum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class AgentPhase(StrEnum):
    """مراحل عمل الوكلاء الموحدة."""
    CONTEXT_ENRICHMENT = "CONTEXT_ENRICHMENT"  # Contextualizer
    PLANNING = "PLANNING"  # Strategist
    REVIEW_PLAN = "REVIEW_PLAN"  # Strategist/Supervisor
    DESIGN = "DESIGN"  # Architect
    EXECUTION = "EXECUTION"  # Operator
    REFLECTION = "REFLECTION"  # Auditor
    RE_PLANNING = "RE_PLANNING"  # LoopController


class AgentRole(StrEnum):
    """أسماء الوكلاء الرسمية (للمحرك والواجهة)."""
    STRATEGIST = "Strategist"
    ARCHITECT = "Architect"
    OPERATOR = "Operator"
    AUDITOR = "Auditor"
    SUPERVISOR = "Supervisor"
    CONTEXTUALIZER = "Contextualizer"
    LOOP_CONTROLLER = "LoopController"


class AgentEventType(StrEnum):
    """أنواع الأحداث المعيارية."""
    PHASE_START = "phase_start"
    PHASE_COMPLETED = "phase_completed"
    LOOP_START = "loop_start"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    MISSION_UPDATE = "mission_update"
    ERROR = "error"


class AgentEventPayload(BaseModel):
    """حمولة الحدث المعيارية."""
    phase: Optional[AgentPhase] = None
    agent: Optional[AgentRole] = None
    iteration: Optional[int] = None
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: str | None = None  # ISO format


class AgentEvent(BaseModel):
    """
    بنية الحدث الموحدة (Envelope).
    تتوافق مع CloudEvents بشكل مبسط.
    """
    type: AgentEventType
    payload: AgentEventPayload
