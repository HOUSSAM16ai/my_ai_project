from unittest.mock import patch

import pytest

from app.services.overmind.code_intelligence.core import StructuralCodeIntelligence


@pytest.fixture
def mock_repo_path(tmp_path):
    d = tmp_path / "repo"
    d.mkdir()
    (d / "main.py").write_text("print('hello')")
    return d


@pytest.mark.asyncio
async def test_analyze_repository_structure(mock_repo_path):
    with patch(
        "app.services.overmind.code_intelligence.core.StructuralCodeIntelligence._analyze_file_metrics"
    ) as mock_metrics:
        mock_metrics.return_value = {"loc": 10, "complexity": 1}

        service = StructuralCodeIntelligence()
        result = await service.analyze_repository(str(mock_repo_path), ["."])

        assert result is not None
        assert "files" in result
        assert len(result["files"]) > 0
