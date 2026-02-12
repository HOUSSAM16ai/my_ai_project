from enum import Enum

from pydantic import BaseModel, Field


class FaultType(str, Enum):
    HOTSPOT = "hotspot"
    MICRO_CRACK = "micro_crack"
    DELAMINATION = "delamination"
    DISCOLORATION = "discoloration"
    NORMAL = "normal"

class FaultDetection(BaseModel):
    fault_type: FaultType
    confidence: float
    bbox: list[int] | None = Field(default=None, description="[x, y, w, h] if applicable")
    description: str

class PanelAnalysisResult(BaseModel):
    image_id: str
    faults: list[FaultDetection]
    overall_status: str  # "Critical", "Warning", "Healthy"
    recommendation: str
