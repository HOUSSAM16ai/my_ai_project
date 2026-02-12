import asyncio
import random

from .models import FaultDetection, FaultType, PanelAnalysisResult


class SolarPanelAnalyzer:
    """
    Analyzes solar panel images for defects.
    This is a Proof of Concept implementation using simulated logic.
    """
    async def analyze_image(self, image_url: str) -> PanelAnalysisResult:
        # Simulate processing delay to mimic real model inference
        await asyncio.sleep(0.1)

        faults: list[FaultDetection] = []
        status = "Healthy"
        rec = "Routine maintenance only."

        image_lower = image_url.lower()

        # Deterministic simulation based on filename keywords
        if "clean" in image_lower:
             status = "Healthy"
             rec = "Routine maintenance only."
        elif "crack" in image_lower or "damaged" in image_lower:
            faults.append(FaultDetection(
                fault_type=FaultType.MICRO_CRACK,
                confidence=0.95,
                bbox=[100, 100, 50, 50],
                description="Micro-crack detected in cell grid."
            ))
            status = "Critical"
            rec = "Immediate replacement recommended to prevent efficiency loss."
        elif "hotspot" in image_lower:
             faults.append(FaultDetection(
                fault_type=FaultType.HOTSPOT,
                confidence=0.89,
                bbox=[200, 150, 40, 40],
                description="Potential hotspot detected."
            ))
             status = "Warning"
             rec = "Inspect physically for shading or cell failure."
        else:
             # Random simulation for generic inputs to demonstrate variety
             # Using a fixed seed based on URL string for deterministic results
             random.seed(sum(ord(c) for c in image_url))
             if random.random() > 0.7:
                 faults.append(FaultDetection(
                     fault_type=FaultType.DISCOLORATION,
                     confidence=0.75,
                     description="Minor discoloration observed."
                 ))
                 status = "Warning"
                 rec = "Monitor for progression."

        return PanelAnalysisResult(
            image_id=image_url,
            faults=faults,
            overall_status=status,
            recommendation=rec
        )
