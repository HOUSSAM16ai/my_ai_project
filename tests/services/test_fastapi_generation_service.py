
import pytest
import os
import time
import json
import tempfile
from unittest.mock import MagicMock, patch, ANY, call, mock_open
from types import SimpleNamespace
from app.services.fastapi_generation_service import (
    MaestroGenerationService,
    get_generation_service,
    StepState,
    OrchestratorTelemetry,
    _safe_json,
    _soft_recover_json,
    _is_stagnation,
    _select_model,
    TaskStatus,
    MissionEventType,
    _ensure_file_tools,
    agent_tools,
    forge_new_code,
    execute_task,
    generate_json,
    generate_comprehensive_response,
    execute_task_legacy_wrapper,
    diagnostics,
)

# ... (Previous fixtures and tests are fine, I'll include them) ...

@pytest.fixture
def mock_llm_client():
    with patch("app.services.fastapi_generation_service.get_llm_client") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        yield client_instance

@pytest.fixture
def mock_db_models():
    with patch("app.services.fastapi_generation_service.log_mission_event") as log_mock, \
         patch("app.services.fastapi_generation_service.finalize_task") as finalize_mock:
        yield log_mock, finalize_mock

@pytest.fixture
def service():
    return MaestroGenerationService()

# --- Existing tests ---

def test_singleton_access():
    s1 = get_generation_service()
    s2 = get_generation_service()
    assert s1 is s2
    assert isinstance(s1, MaestroGenerationService)

def test_step_state():
    state = StepState(step_index=1)
    state.finish()
    assert state.duration_ms is not None

def test_telemetry_to_dict():
    tel = OrchestratorTelemetry(steps_taken=5, error="Some error")
    d = tel.to_dict()
    assert d["steps_taken"] == 5

def test_safe_json():
    assert _safe_json("already string") == "already string"
    assert _safe_json({"a": 1}) == '{\n  "a": 1\n}'

def test_soft_recover_json():
    assert _soft_recover_json('{"key": "value"}') == '{"key": "value"}'

def test_is_stagnation():
    assert _is_stagnation([], ["tool1"]) is False
    assert _is_stagnation(["tool1"], ["tool1"]) is True

def test_select_model():
    with patch.dict(os.environ, {}, clear=True):
        assert _select_model() == "openai/gpt-4o"

def test_text_completion_success(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = "Response"
    assert service.text_completion("Sys", "User") == "Response"

def test_text_completion_failure_retry(service, mock_llm_client):
    mock_llm_client.chat.completions.create.side_effect = [RuntimeError("Temp"), MagicMock(choices=[MagicMock(message=MagicMock(content="Rec"))])]
    assert service.text_completion("Sys", "User", max_retries=1) == "Rec"

def test_text_completion_failure_fail_hard(service, mock_llm_client):
    mock_llm_client.chat.completions.create.side_effect = RuntimeError("Fatal")
    with pytest.raises(RuntimeError):
        service.text_completion("Sys", "User", max_retries=0, fail_hard=True)

def test_structured_json_success(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = '{"answer": 42}'
    assert service.structured_json("Sys", "User", {"required": ["answer"]}) == {"answer": 42}

def test_structured_json_soft_recover(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = '```json\n{"answer": 42}\n```'
    assert service.structured_json("Sys", "User", {"required": ["answer"]}) == {"answer": 42}

def test_structured_json_missing_required(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = '{"other": 1}'
    assert service.structured_json("Sys", "User", {"required": ["answer"]}, max_retries=0) is None

def test_forge_new_code_success(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = "Code"
    assert service.forge_new_code("Prompt")["status"] == "success"

def test_forge_new_code_error(service, mock_llm_client):
    mock_llm_client.chat.completions.create.side_effect = RuntimeError("Error")
    assert service.forge_new_code("Prompt")["status"] == "error"

def test_generate_comprehensive_response_success(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = "Answer"
    assert service.generate_comprehensive_response("Prompt")["status"] == "success"

def test_generate_comprehensive_response_error(service, mock_llm_client):
    mock_llm_client.chat.completions.create.side_effect = RuntimeError("Error")
    assert service.generate_comprehensive_response("Prompt")["status"] == "error"

def test_execute_task_legacy_wrapper_method(service, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = "Legacy"
    assert service.execute_task_legacy_wrapper({"description": "D"})["status"] == "ok"
    assert service.execute_task_legacy_wrapper({})["status"] == "error"

def test_diagnostics(service):
    assert "version" in service.diagnostics()

def test_execute_task_success_no_tools(service, mock_llm_client, mock_db_models):
    log_mission_event_mock, finalize_task_mock = mock_db_models
    task = MagicMock()
    task.id = "task-1"

    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = "Done."
    mock_llm_client.chat.completions.create.return_value.choices[0].message.tool_calls = None

    with patch.dict(os.environ, {"MAESTRO_EMIT_TASK_EVENTS": "1"}):
        service.execute_task(task)

    log_mission_event_mock.assert_any_call(ANY, MissionEventType.TASK_STATUS_CHANGE, payload={"task_id": "task-1", "status": "RUNNING"})
    finalize_task_mock.assert_called_with(task, status=TaskStatus.SUCCESS, result_text="Done.")

def test_execute_task_with_tools(service, mock_llm_client, mock_db_models):
    _, finalize_task_mock = mock_db_models
    task = MagicMock()

    class MockToolCall:
        def __init__(self, name, args):
            self.id = "1"
            self.function = SimpleNamespace(name=name, arguments=args)
        def model_dump(self): return {"id": "1", "function": {"name": self.function.name, "arguments": self.function.arguments}}

    msg1 = MagicMock()
    msg1.tool_calls = [MockToolCall("read_file", '{"path": "p"}')]

    msg2 = MagicMock()
    msg2.tool_calls = None
    msg2.content = "Done"

    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=msg1)]),
        MagicMock(choices=[MagicMock(message=msg2)])
    ]

    with patch("app.services.fastapi_generation_service._invoke_tool") as mock_invoke:
        mock_invoke.return_value = MagicMock(to_dict=lambda: {"ok": True})
        with patch("app.services.fastapi_generation_service.agent_tools.resolve_tool_name", side_effect=lambda x: x), \
             patch("app.services.fastapi_generation_service.agent_tools.get_tools_schema", return_value=[]):
            service.execute_task(task)
            mock_invoke.assert_called_with("read_file", {"path": "p"})
            finalize_task_mock.assert_called_with(task, status=TaskStatus.SUCCESS, result_text="Done")

def test_execute_task_max_steps_exhausted(service, mock_llm_client, mock_db_models):
    _, finalize_task_mock = mock_db_models
    task = MagicMock()

    class MockToolCall:
        def __init__(self, id, name):
            self.id = id
            self.function = SimpleNamespace(name=name, arguments='{}')
        def model_dump(self): return {"id": self.id, "function": {"name": self.function.name, "arguments": '{}'}}

    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(tool_calls=[MockToolCall("1", "t1")]))]),
        MagicMock(choices=[MagicMock(message=MagicMock(tool_calls=[MockToolCall("2", "t2")]))]),
        MagicMock(choices=[MagicMock(message=MagicMock(tool_calls=[MockToolCall("3", "t3")]))])
    ]

    with patch("app.services.fastapi_generation_service._cfg", return_value=2), \
         patch("app.services.fastapi_generation_service._invoke_tool") as invoke_mock, \
         patch("app.services.fastapi_generation_service.agent_tools.resolve_tool_name", side_effect=lambda x: x), \
         patch("app.services.fastapi_generation_service.agent_tools.get_tools_schema", return_value=[]):
        invoke_mock.return_value = MagicMock(to_dict=lambda: {"ok": True})
        service.execute_task(task)
        assert task.result["final_reason"] == "max_steps_exhausted"

def test_execute_task_stagnation(service, mock_llm_client, mock_db_models):
    _, finalize_task_mock = mock_db_models
    task = MagicMock()

    class MockToolCall:
        def __init__(self):
            self.id = "1"
            self.function = SimpleNamespace(name="t", arguments='{}')
        def model_dump(self): return {"id": "1", "function": {"name": "t", "arguments": '{}'}}

    mock_llm_client.chat.completions.create.return_value.choices[0].message.tool_calls = [MockToolCall()]

    with patch("app.services.fastapi_generation_service._invoke_tool") as invoke_mock, \
         patch("app.services.fastapi_generation_service.agent_tools.resolve_tool_name", side_effect=lambda x: x), \
         patch("app.services.fastapi_generation_service.agent_tools.get_tools_schema", return_value=[]), \
         patch.dict(os.environ, {"MAESTRO_STAGNATION_ENFORCE": "1"}):
        invoke_mock.return_value = MagicMock(to_dict=lambda: {"ok": True})
        service.execute_task(task)
        assert task.result["final_reason"] == "stagnation_detected"

def test_build_bilingual_error_message(service):
    assert "Timeout" in service._build_bilingual_error_message("Timeout", 1, 1)

def test_ensure_file_tools():
    original_reg = getattr(agent_tools, "_TOOL_REGISTRY", {}).copy()
    try:
        agent_tools._TOOL_REGISTRY = {}
        _ensure_file_tools()

        reg = agent_tools._TOOL_REGISTRY

        # Write handler
        write_handler = reg["write_file"]["handler"]
        with patch("builtins.open", mock_open()) as m_open, patch("os.makedirs"):
            res = write_handler("test.txt", "content")
            assert res.ok is True
            m_open.assert_called_with("/app/test.txt", "w", encoding="utf-8")

        # Read handler
        read_handler = reg["read_file"]["handler"]
        with patch("builtins.open", mock_open(read_data="content")) as m_open, \
             patch("os.path.exists", return_value=True):
            res = read_handler("test.txt")
            assert res.ok is True
            assert res.data["content"] == "content"

    finally:
        agent_tools._TOOL_REGISTRY = original_reg

def test_build_context_blob(service):
    task = MagicMock()
    task.description = "Task desc"
    task.mission.deep_index_summary = "Deep summary"
    task.mission.deep_index_meta = {"hotspots_count": 5}

    with patch("app.services.fastapi_generation_service.system_service") as mock_sys_svc:
        mock_sys_svc.find_related_context.return_value.data = {"context": "base"}

        with patch.dict(os.environ, {"MAESTRO_ATTACH_DEEP_INDEX": "1", "MAESTRO_HOTSPOT_HINT": "1"}):
            telemetry = OrchestratorTelemetry()
            blob = service._build_context_blob(task, True, telemetry)
            assert blob["context"] == "base"
            assert blob["_deep_index_excerpt"] == "Deep summary"
            assert telemetry.hotspot_hint_used is True

def test_global_wrappers(mock_llm_client):
    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = "Forged"
    assert forge_new_code("prompt")["status"] == "success"

    mock_llm_client.chat.completions.create.return_value.choices[0].message.content = '{"a":1}'
    assert generate_json("prompt")["status"] == "success"

    assert generate_comprehensive_response("prompt")["status"] == "success"

    assert execute_task_legacy_wrapper("description")["status"] == "ok"

    assert "version" in diagnostics()

def test_execute_task_wrapper(mock_llm_client, mock_db_models):
    task = MagicMock()
    task.id = "task-wrap"
    with patch.dict(os.environ, {"MAESTRO_EMIT_TASK_EVENTS": "0"}):
        execute_task(task)
    assert "telemetry" in task.result

def test_execute_task_tool_call_limit(service, mock_llm_client, mock_db_models):
    _, finalize_task_mock = mock_db_models
    task = MagicMock()

    class MockToolCall:
        def __init__(self, id, name):
            self.id = id
            self.function = SimpleNamespace(name=name, arguments='{}')
        def model_dump(self): return {"id": self.id, "function": {"name": self.function.name, "arguments": '{}'}}

    # Setup many tool calls
    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(tool_calls=[MockToolCall("1", "t1")]))]),
        MagicMock(choices=[MagicMock(message=MagicMock(tool_calls=[MockToolCall("2", "t2")]))]),
    ]

    with patch.dict(os.environ, {"MAESTRO_TOOL_CALL_LIMIT": "1"}), \
         patch("app.services.fastapi_generation_service._invoke_tool") as mock_invoke, \
         patch("app.services.fastapi_generation_service.agent_tools.resolve_tool_name", side_effect=lambda x: x), \
         patch("app.services.fastapi_generation_service.agent_tools.get_tools_schema", return_value=[]):
        mock_invoke.return_value = MagicMock(to_dict=lambda: {"ok": True})

        service.execute_task(task)

        assert task.result["final_reason"] == "tool_limit_reached"
        finalize_task_mock.assert_called_with(task, status=TaskStatus.FAILED, result_text="(no answer produced)")

def test_execute_task_catastrophic_failure(service, mock_llm_client, mock_db_models):
    task = MagicMock()
    mock_llm_client.chat.completions.create.side_effect = RuntimeError("Catastrophe")

    service.execute_task(task)

    assert task.result["error"] == "Catastrophe"
    # finalize_task should be called with FAILED and the message
    _, finalize_task_mock = mock_db_models

    # We check if called with status=FAILED and result_text containing the error
    call_args = finalize_task_mock.call_args
    assert call_args is not None
    args, kwargs = call_args
    assert kwargs["status"] == TaskStatus.FAILED
    assert "Catastrophic failure" in kwargs["result_text"]
