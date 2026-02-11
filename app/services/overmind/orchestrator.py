# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE
# Version: 12.1.0-super-agent (Refactored)
# =================================================================================================

"""
منسق العقل المدبر (Overmind Orchestrator).

هذه الفئة تمثل مركز القيادة والسيطرة للوكلاء المستقلين.
تقوم بإدارة دورة حياة "المهمة" (Mission) بالكامل من خلال تنسيق العمل بين الأنظمة الفرعية:
التخطيط (Planning) والتنفيذ (Execution).

المعايير الرئيسية:
- Abstraction: تفويض كامل للمنطق المعرفي إلى `SuperBrain`.
- Strictness: عدم وجود منطق "Legacy" أو مسارات بديلة.
- Resilience: معالجة شاملة للأخطاء على المستوى الأعلى.
- Dependency Inversion: الاعتماد على البروتوكولات.
"""

import logging
from typing import TYPE_CHECKING

from app.core.domain.mission import Mission, MissionEventType, MissionStatus
from app.core.protocols import MissionStateManagerProtocol, TaskExecutorProtocol
from app.services.overmind.domain.enums import OvermindMessage

if TYPE_CHECKING:
    from app.services.overmind.domain.cognitive import SuperBrain
    from app.services.overmind.langgraph.engine import LangGraphOvermindEngine

logger = logging.getLogger(__name__)

__all__ = ["OvermindOrchestrator"]


class OvermindOrchestrator:
    """
    منسق العقل المدبر (The Cognitive Brain).

    يعمل هذا الصف كجسر بين "الرغبة" (User Intent) و "الواقع" (System Actions).
    لا يحتوي على منطق معقد بحد ذاته، بل يقوم بتفويض المهام لمكونات متخصصة (Brain, Executor, State).
    """

    def __init__(
        self,
        *,
        state_manager: MissionStateManagerProtocol,
        executor: TaskExecutorProtocol,
        brain: "SuperBrain | LangGraphOvermindEngine",
    ) -> None:
        """
        تهيئة المنسق مع التبعيات اللازمة.

        Args:
            state_manager (MissionStateManagerProtocol): مدير حالة المهمة.
            executor (TaskExecutorProtocol): الذراع التنفيذي.
            brain (SuperBrain | LangGraphOvermindEngine): العقل المفكر (Council of Wisdom).
        """
        self.state = state_manager
        self.executor = executor
        self.brain = brain

    async def run_mission(self, mission_id: int, force_research: bool = False) -> None:
        """
        نقطة الدخول الرئيسية لدورة حياة المهمة غير المتزامنة.
        تقوم بتفويض الحمل المعرفي للعقل الخارق (SuperBrain).

        Args:
            mission_id (int): معرف المهمة في قاعدة البيانات.
            force_research (bool): إجبار النظام على إجراء بحث (Internet/DB).
        """
        try:
            mission = await self.state.get_mission(mission_id)
            if not mission:
                logger.error(f"Mission {mission_id} not found.")
                return

            # --- Layer C: Provider Readiness Gate ---
            from app.services.overmind.readiness import check_mission_readiness

            readiness_check = await check_mission_readiness()

            if not readiness_check.get("ready"):
                error_reason = readiness_check.get("error", "Failed readiness check")
                logger.error(
                    f"Mission {mission_id} aborted due to readiness failure: {error_reason}"
                )

                await self.state.update_mission_status(
                    mission_id, MissionStatus.FAILED, note=f"Readiness Check Failed: {error_reason}"
                )
                await self.state.log_event(
                    mission_id,
                    MissionEventType.MISSION_FAILED,
                    {"error": error_reason, "reason": "readiness_gate_failure"},
                )
                return

            # Log degraded mode if applicable
            if readiness_check.get("mode") == "degraded":
                await self.state.log_event(
                    mission_id,
                    MissionEventType.STATUS_CHANGE,
                    {
                        "info": "Mission running in Degraded Mode (No Tavily Key found). Expecting potentially lower quality search results.",
                        "mode": "degraded",
                    },
                )
            # ----------------------------------------

            await self._run_super_agent_loop(mission, force_research=force_research)

        except Exception as e:
            # Catch-all for catastrophic failures preventing the loop from starting
            logger.exception(f"Catastrophic failure in Mission {mission_id}")
            # Fix: Rollback session to prevent "current transaction is aborted" errors
            if hasattr(self.state, "session"):
                try:
                    await self.state.session.rollback()
                except Exception as rollback_ex:
                    logger.error(f"Failed to rollback session: {rollback_ex}")

            await self.state.update_mission_status(
                mission_id, MissionStatus.FAILED, note=f"Fatal Error: {e}"
            )
            await self.state.log_event(
                mission_id,
                MissionEventType.MISSION_FAILED,
                {"error": str(e), "reason": "catastrophic_crash"},
            )

    async def _run_super_agent_loop(self, mission: Mission, force_research: bool = False) -> None:
        """
        الحلقة الذاتية المدفوعة بمجلس الحكمة (Council of Wisdom).

        Args:
            mission (Mission): كائن المهمة.
            force_research (bool): إجبار البحث.
        """
        await self.state.update_mission_status(
            mission.id, MissionStatus.RUNNING, OvermindMessage.CONVENING_COUNCIL
        )

        async def _log_bridge(evt_type: str, payload: dict[str, object]) -> None:
            """
            جسر (Bridge) للربط بين أحداث العقل ومدير الحالة.
            """
            await self.state.log_event(
                mission.id,
                MissionEventType.STATUS_CHANGE,
                {"brain_event": evt_type, "data": payload},
            )

        try:
            # تفويض كامل للعقل (Abstraction Barrier)
            # Support for both Legacy SuperBrain and New LangGraph Engine
            if hasattr(self.brain, "run"):
                # LangGraph Path
                initial_context = self._build_initial_context(mission)
                # Inject Force Research Flag
                if force_research:
                    initial_context["force_research"] = True

                run_result = await self.brain.run(
                    run_id=str(mission.id),
                    objective=mission.objective,
                    context=initial_context,
                    constraints=[],
                    priority="normal",
                    observer=_log_bridge,
                )
                # Convert LangGraph state to result dict
                result = run_result.state
            else:
                # Legacy SuperBrain Path
                result = await self.brain.process_mission(mission, log_event=_log_bridge)

            # Extract summary for Admin Dashboard visibility
            summary = self._extract_summary(result)

            # Determine final status based on execution evidence (Success-by-Evidence)
            # --- Layer B: Outcome Arbiter ---
            final_status = self._arbitrate_mission_outcome(result, mission.id)

            await self.state.complete_mission(
                mission.id,
                result_summary=summary,
                result_json=result,
                status=final_status,
            )

        except Exception as e:
            logger.exception(f"SuperBrain failure in mission {mission.id}: {e}")
            # Fix: Rollback session to prevent "current transaction is aborted" errors
            if hasattr(self.state, "session"):
                try:
                    await self.state.session.rollback()
                except Exception as rollback_ex:
                    logger.error(f"Failed to rollback session: {rollback_ex}")

            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, f"Cognitive Error: {e}"
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.MISSION_FAILED,
                {"error": str(e), "error_type": type(e).__name__},
            )

    def _arbitrate_mission_outcome(
        self, result: dict[str, object], mission_id: int
    ) -> MissionStatus:
        """
        Arbiter: Decides the final mission status based on evidence.
        Enforces "Outcome/Progress Divergence" prevention.
        """
        execution = result.get("execution")

        # Default assumption
        status = MissionStatus.SUCCESS

        # 1. Check for explicit OperatorAgent failure flags
        if isinstance(execution, dict):
            exec_status = execution.get("status")
            if exec_status == "failed":
                logger.error(f"Mission {mission_id} FAILED: Operator reported total failure.")
                return MissionStatus.FAILED
            if exec_status == "partial_failure":
                logger.warning(
                    f"Mission {mission_id} PARTIAL_SUCCESS: Operator reported partial failures."
                )
                status = MissionStatus.PARTIAL_SUCCESS

        # 2. Check for Empty Search Results (Crucial for "No Tavily" scenarios)
        # If the plan involved search, but we got no results, it's not a full success.
        # We inspect the execution results for search tool calls that returned empty lists/strings.
        if isinstance(execution, dict) and "results" in execution:
            results_list = execution.get("results", [])
            for task_res in results_list:
                if isinstance(task_res, dict):
                    tool_name = task_res.get("tool")
                    # If search was attempted
                    if tool_name in (
                        "search_content",
                        "search_educational_content",
                        "deep_research",
                    ):
                        tool_output = task_res.get("result", {})
                        if isinstance(tool_output, dict):
                            # Executor wrapper format
                            raw_data = tool_output.get("result_data")
                            if not raw_data or (isinstance(raw_data, list) and len(raw_data) == 0):
                                logger.warning(
                                    f"Mission {mission_id} PARTIAL_SUCCESS: Search tool '{tool_name}' returned empty results."
                                )
                                status = MissionStatus.PARTIAL_SUCCESS

        return status

    def _extract_summary(self, result: dict[str, object]) -> str:
        """
        استخراج ملخص نصي للنتيجة لعرضه في لوحة الإدارة.
        Extracts a text summary for the Admin Dashboard.
        """
        if not result:
            return "تمت المهمة بنجاح."

        # 1. Try explicit summary/output fields
        if result.get("summary"):
            return str(result["summary"])
        if result.get("output"):
            return str(result["output"])
        if result.get("answer"):
            return str(result["answer"])

        # 2. Support LangGraph State Structure (nested execution report)
        execution = result.get("execution")
        if isinstance(execution, dict) and "results" in execution:
            # Flatten execution results for the summary logic below
            result_results = execution["results"]
        else:
            result_results = result.get("results")

        # 3. Handle OperatorAgent results list
        if result_results and isinstance(result_results, list):
            lines = [f"✅ Executed {len(result_results)} tasks:"]
            for t in result_results:
                if isinstance(t, dict):
                    name = t.get("name", "Task")
                    res = t.get("result", {})
                    # If result is a dict with result_text (Executor format)
                    val = res.get("result_text") if isinstance(res, dict) else str(res)
                    # Truncate if too long
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    lines.append(f"- {name}: {val_str}")
            return "\n".join(lines)

        # 4. Fallback to string representation
        return str(result)[:500]

    def _build_initial_context(self, mission: Mission) -> dict[str, object]:
        """
        بناء سياق أولي غني لتمريره إلى محرك LangGraph.
        """
        return {
            "mission_id": mission.id,
            "objective": mission.objective,
            "metadata_filters": {},
            "max_iterations": 3,
        }
