from enum import Enum
from typing import List, Optional
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
    bbox: Optional[List[int]] = Field(default=None, description="[x, y, w, h] if applicable")
    description: str

class PanelAnalysisResult(BaseModel):
    image_id: str
    faults: List[FaultDetection]
    overall_status: str  # "Critical", "Warning", "Healthy"
    recommendation: str
