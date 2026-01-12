
import pytest

from app.core.prompts import OVERMIND_SYSTEM_PROMPT, get_static_system_prompt, get_system_prompt


@pytest.mark.asyncio
async def test_get_system_prompt_static():
    prompt = get_static_system_prompt(include_health=True)
    assert "OVERMIND CLI MINDGATE" in prompt
    assert "المبادئ الصارمة للنظام" in prompt
    assert "## ⏰ Time:" in prompt
    assert "PROJECT METRICS" not in prompt

@pytest.mark.asyncio
async def test_get_system_prompt_async_default():
    prompt = await get_system_prompt(include_health=True, include_dynamic=False)
    assert "OVERMIND CLI MINDGATE" in prompt
    assert "المبادئ الصارمة للنظام" in prompt
    assert "## ⏰ Time:" in prompt
    assert "PROJECT METRICS" not in prompt

@pytest.mark.asyncio
async def test_get_system_prompt_async_dynamic():
    # We test that it runs without error.
    # The actual content of metrics depends on environment, but the header should be there.
    prompt = await get_system_prompt(include_health=True, include_dynamic=True)
    assert "OVERMIND CLI MINDGATE" in prompt
    assert "المبادئ الصارمة للنظام" in prompt
    # Structure is included in dynamic
    assert "PROJECT STRUCTURE" in prompt
    # Metrics might fail gracefully (returning empty string) if git is not present or other issues,
    # but the function should not crash.
    # Our refactored code adds "PROJECT METRICS" header only if successful?
    # Wait, let's check code.
    # It adds result of _get_dynamic_metrics().
    # _get_dynamic_metrics returns formatted string starting with "## 🔬 PROJECT METRICS".
    # Or empty string if exception.

    # Since we are in an environment where git might be available or mocked, let's just check it doesn't crash.
    # and if it returns something, it should be a string.
    assert isinstance(prompt, str)

def test_global_constant():
    assert "OVERMIND CLI MINDGATE" in OVERMIND_SYSTEM_PROMPT
