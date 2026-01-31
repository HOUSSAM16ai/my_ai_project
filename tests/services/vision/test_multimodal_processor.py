import json
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from app.services.vision.multimodal_processor import (
    ImageAnalysis,
    MultiModalProcessor,
    get_multimodal_processor,
)


@pytest.fixture
def mock_ai_client():
    return AsyncMock()

@pytest.fixture
def processor(mock_ai_client):
    return MultiModalProcessor(ai_client=mock_ai_client)

def test_singleton_instance():
    p1 = get_multimodal_processor()
    p2 = get_multimodal_processor()
    assert p1 is p2
    assert isinstance(p1, MultiModalProcessor)

@pytest.mark.asyncio
async def test_analyze_image_success(processor, mock_ai_client):
    # Mock file existence and read
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=b"fake_image_data")):

        # Mock AI response
        expected_json = {
            "text_content": "Solve x+1=2",
            "equations": ["x+1=2"],
            "diagrams": [],
            "exercise_type": "algebra",
            "subject": "math",
            "confidence": 0.9
        }
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(expected_json)
        mock_ai_client.generate.return_value = mock_response

        result = await processor.analyze_image("test.jpg")

        assert result.text_content == "Solve x+1=2"
        assert result.equations == ["x+1=2"]
        assert result.confidence == 0.9
        mock_ai_client.generate.assert_awaited_once()

@pytest.mark.asyncio
async def test_analyze_image_no_client():
    p = MultiModalProcessor(ai_client=None)
    result = await p.analyze_image("test.jpg")
    assert result.confidence == 0.0
    assert result.text_content == ""

@pytest.mark.asyncio
async def test_analyze_image_file_not_found(processor):
    with patch("pathlib.Path.exists", return_value=False):
        result = await processor.analyze_image("missing.jpg")
        assert result.confidence == 0.0

@pytest.mark.asyncio
async def test_analyze_image_ai_error(processor, mock_ai_client):
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=b"data")):

        mock_ai_client.generate.side_effect = Exception("AI Error")
        result = await processor.analyze_image("test.jpg")
        assert result.confidence == 0.0

@pytest.mark.asyncio
async def test_extract_exercise_from_image(processor, mock_ai_client):
    # Reuse success logic
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=b"data")):

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "text_content": "Content",
            "equations": ["E=mc2"],
            "diagrams": ["Graph"],
            "exercise_type": "Physics",
            "subject": "Science",
            "confidence": 0.8
        })
        mock_ai_client.generate.return_value = mock_response

        data = await processor.extract_exercise_from_image("test.jpg")

        assert data["success"] is True
        assert data["text"] == "Content"
        assert "E=mc2" in data["formatted"]
        assert "Graph" in data["formatted"]

def test_fallback_analysis_structure(processor):
    fallback = processor._fallback_analysis()
    assert isinstance(fallback, ImageAnalysis)
    assert fallback.confidence == 0.0
