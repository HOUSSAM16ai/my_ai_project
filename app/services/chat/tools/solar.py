from langchain_core.tools import tool

from app.services.solar import SolarPanelAnalyzer

analyzer = SolarPanelAnalyzer()

@tool("detect_solar_faults")
async def detect_solar_faults(image_url: str) -> dict:
    """
    Analyzes an image of a solar panel to detect faults like hotspots or cracks.

    Args:
        image_url (str): The URL or path to the solar panel image.

    Returns:
        dict: Analysis result containing detected faults and recommendations.
    """
    result = await analyzer.analyze_image(image_url)
    return result.model_dump()
