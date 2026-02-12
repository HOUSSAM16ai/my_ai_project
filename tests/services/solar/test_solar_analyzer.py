import pytest

from app.services.solar import FaultType, SolarPanelAnalyzer


@pytest.mark.asyncio
async def test_detect_cracks():
    analyzer = SolarPanelAnalyzer()
    result = await analyzer.analyze_image("path/to/cracked_panel.jpg")

    assert result.overall_status == "Critical"
    assert len(result.faults) == 1
    assert result.faults[0].fault_type == FaultType.MICRO_CRACK

@pytest.mark.asyncio
async def test_detect_hotspots():
    analyzer = SolarPanelAnalyzer()
    result = await analyzer.analyze_image("https://example.com/images/hotspot_detected.png")

    assert result.overall_status == "Warning"
    assert len(result.faults) == 1
    assert result.faults[0].fault_type == FaultType.HOTSPOT

@pytest.mark.asyncio
async def test_healthy_panel():
    analyzer = SolarPanelAnalyzer()
    # "clean" triggers healthy logic
    result = await analyzer.analyze_image("clean_panel_v2.jpg")

    assert result.overall_status == "Healthy"
    assert len(result.faults) == 0
