current_app.logger.info(f"[Maestro] Executing Task #{task.id} for Mission #{mission.id}")
task.status = TaskStatus.RUNNING
log_mission_event(mission, MissionEventType.TASK_STATUS_CHANGE, payload={"task_id": task.id, "status": "RUNNING"})
db.session.commit()

try:
    client = get_llm_client()
    code_ctx_res = system_service.find_related_context(task.description)
    
    identity_prompt = {"role": "system", "content": _format_identity_block(task, code_ctx_res.data)}
    messages: List[Dict[str, Any]] = [identity_prompt, {"role": "user", "content": task.description}]
    tools_schema = agent_tools.get_tools_schema()

    for step_idx in range(cfg.max_steps):
        state = StepState(step_index=step_idx)
        step_states.append(state)
        telemetry.steps_taken = step_idx + 1
        
        # Sanitize messages before API call
        for m in messages:
            if m.get("content") is None: m["content"] = ""
        
        llm_response = client.chat.completions.create(model=cfg.model_name, messages=messages, tools=tools_schema, tool_choice="auto")
        raw_response_message = llm_response.choices[0].message
        tool_calls = getattr(raw_response_message, "tool_calls", None) or []
        
        assistant_dict = _normalize_assistant_message(raw_response_message)
        messages.append(assistant_dict)
        log_mission_event(mission, MissionEventType.TASK_UPDATED, payload={"task_id": task.id, "step": step_idx, "decision": assistant_dict}, note="Maestro reasoning step.")

        if tool_calls:
            state.decision = "tool"
            new_tool_names = [call.function.name for call in tool_calls]

            # Stagnation & Repetition Guards (as before)
            if _detect_no_progress(previous_tool_names_snapshot, new_tool_names) or any(tool_usage_sequence[-cfg.max_repeated_tool:].count(t) >= cfg.max_repeated_tool for t in new_tool_names):
                telemetry.finalization_reason = "stagnation_detected"
                break # Exit loop

            previous_tool_names_snapshot = new_tool_names
            tool_usage_sequence.extend(new_tool_names)
            
            for call in tool_calls:
                tool_result = _invoke_tool(call.function.name, json.loads(call.function.arguments))
                messages.append({"role": "tool", "tool_call_id": call.id, "name": call.function.name, "content": _serialize_safe(tool_result.to_dict())})
                log_mission_event(mission, MissionEventType.TASK_UPDATED, payload={"task_id": task.id, "tool_result": tool_result.to_dict()}, note=f"Tool '{call.function.name}' executed.")
            continue
        else:
            state.decision = "final"
            final_answer = assistant_dict.get("content") or "(no textual content)"
            telemetry.finalization_reason = "model_concluded"
            state.finish()
            break
    else:
        telemetry.finalization_reason = "max_steps_exhausted"
    
    finalize_task(
        task, status=TaskStatus.SUCCESS, result_text=final_answer,
        result_meta={"telemetry": telemetry.to_dict(), "steps": [asdict(s) for s in step_states]}
    )
    db.session.commit()

except Exception as e:
    current_app.logger.error(f"[Maestro] Catastrophic failure on Task #{task.id}: {e}", exc_info=True)
    finalize_task(
        task, status=TaskStatus.FAILED, result_text=f"Catastrophic failure: {e}",
        result_meta={"trace": traceback.format_exc()}
    )
    db.session.commit()