# app/cli/mindgate_commands.py
# ======================================================================================
# MINDGATE COMMAND SUITE v105.0 "HyperGate++ FixPack"
# ======================================================================================
# PURPOSE:
#   واجهة أوامر موحدة للتحكم في:
#     - Overmind Missions (إنشاء / متابعة / إعادة التخطيط)
#     - طبقة التخطيط (Planners) عبر factory
#     - Maestro LLM / Generation (forge_new_code + legacy wrapper + json)
#     - الأدوات (agent_tools) والفهرسة (system_service)
#
# WHAT'S NEW (v105.0 vs v104.0):
#   1. إصلاح خطأ TypeError مع Pydantic v2:
#        model_dump_json() لا يقبل ensure_ascii -> تمت إزالته.
#   2. إضافة دالة _dump_plan_json تدعم:
#        - Pydantic v2 (model_dump_json(indent=2))
#        - Pydantic v1 (dict() + json.dumps)
#        - Fallback لأي كائن آخر.
#   3. تصحيح نسيان استيراد uuid المستخدم في ask_command (كان سيؤدي إلى NameError).
#   4. إخراج JSON أكثر أماناً للخطة عند --json-output.
#   5. الحفاظ على بقية السلوكيات دون تغيير.
#
# ENV FLAGS:
#   MINDGATE_DEBUG=1            => إظهار Tracebacks
#   MINDGATE_RELAX_IMPORTS=1    => تجاوز أعطال الاستيراد غير الحرجة
#   MINDGATE_DEFAULT_PLANNER=.. => اختيار مخطط افتراضي
#
# ======================================================================================
from __future__ import annotations

import difflib
import importlib
import json
import os
import time
import traceback
import uuid
from types import ModuleType
from typing import Any

import click
from flask import Blueprint

# ======================================================================================
# ENV FLAGS
# ======================================================================================
MINDGATE_DEBUG = bool(int(os.environ.get("MINDGATE_DEBUG", "0") or "0"))
MINDGATE_RELAX_IMPORTS = bool(int(os.environ.get("MINDGATE_RELAX_IMPORTS", "0") or "0"))
DEFAULT_PLANNER_NAME = os.environ.get("MINDGATE_DEFAULT_PLANNER", "maestro_graph_planner_v2")

# ======================================================================================
# BLUEPRINT
# ======================================================================================
mindgate_cli = Blueprint("mindgate", __name__, cli_group="mindgate")


# ======================================================================================
# COLOR HELPERS
# ======================================================================================
def C_RED(s):
    click.secho(s, fg="red", err=True)


def C_GREEN(s):
    click.secho(s, fg="green")


def C_YELLOW(s):
    click.secho(s, fg="yellow")


def C_CYAN(s):
    click.secho(s, fg="cyan")


def C_MAGENTA(s):
    click.secho(s, fg="magenta")


def C_DIM(s):
    click.secho(s, fg="white", dim=True)


def C_BLUE(s):
    click.secho(s, fg="blue")


# ======================================================================================
# IMPORT / SERVICE LOADING STATE
# ======================================================================================
class ImportRecord:
    def __init__(self, name: str):
        self.name = name
        self.ok = False
        self.error: BaseException | None = None
        self.trace: str | None = None
        self.module: ModuleType | None = None

    def to_dict(self):
        return {
            "name": self.name,
            "ok": self.ok,
            "error": repr(self.error) if self.error else None,
            "trace": self.trace if (MINDGATE_DEBUG) else None,
        }


IMPORTS: dict[str, ImportRecord] = {}
SERVICES_READY = False
DB_READY = False

# Bound modules / symbols
generation_service = None
system_service = None
agent_tools = None
overmind = None
planning = None
MissionPlanSchema = None
PlanWarning = None

db = None
User = Mission = MissionPlan = Task = None
MissionStatus = TaskStatus = None

# ======================================================================================
# MODULE LISTS
# ======================================================================================
SERVICE_MODULES = [
    "app.services.generation_service",
    "app.services.system_service",
    "app.services.agent_tools",
    "app.services.master_agent_service",
]

PLANNING_MODULES = [
    "app.overmind.planning.schemas",
    "app.overmind.planning.factory",
    "app.overmind.planning.llm_planner",
]

DB_MODULES = [
    "app",
    "app.models",
]


# ======================================================================================
# IMPORT HELPERS
# ======================================================================================
def _import_module(path: str) -> ImportRecord:
    rec = IMPORTS.get(path) or ImportRecord(path)
    try:
        rec.module = importlib.import_module(path)
        rec.ok = True
    except Exception as e:
        rec.error = e
        rec.trace = traceback.format_exc()
    IMPORTS[path] = rec
    return rec


def _root_cause_summary() -> list[str]:
    msgs = []
    for rec in IMPORTS.values():
        if not rec.ok and rec.error:
            msgs.append(f"{rec.name}: {type(rec.error).__name__}: {rec.error}")
    return msgs


def _debug_print_imports():
    for name, rec in IMPORTS.items():
        status = "OK" if rec.ok else "FAIL"
        fn = C_GREEN if rec.ok else C_RED
        fn(f"[{status}] {name}")
        if not rec.ok:
            C_YELLOW(f"  Error: {rec.error}")
            if MINDGATE_DEBUG:
                C_DIM(rec.trace or "")


def _maybe_suggest_planner(name: str, available: list[str]) -> str | None:
    if not available:
        return None
    matches = difflib.get_close_matches(name, available, n=1, cutoff=0.45)
    return matches[0] if matches else None


# ======================================================================================
# LOADING / ENSURE
# ======================================================================================
def load_services(force: bool = False):
    global SERVICES_READY, DB_READY
    global generation_service, system_service, agent_tools, overmind, planning
    global MissionPlanSchema, PlanWarning
    global db, User, Mission, MissionPlan, Task, MissionStatus, TaskStatus

    if SERVICES_READY and DB_READY and not force:
        return

    # DB
    for m in DB_MODULES:
        _import_module(m)
    if IMPORTS.get("app.models") and IMPORTS["app.models"].ok:
        try:
            from app import db as _db
            from app.models import Mission as _Mission
            from app.models import MissionPlan as _MissionPlan
            from app.models import MissionStatus as _MissionStatus
            from app.models import Task as _Task
            from app.models import TaskStatus as _TaskStatus
            from app.models import User as _User

            db = _db
            User, Mission, MissionPlan, Task = _User, _Mission, _MissionPlan, _Task
            MissionStatus, TaskStatus = _MissionStatus, _TaskStatus
            DB_READY = True
        except Exception as e:
            IMPORTS["app.models"].ok = False
            IMPORTS["app.models"].error = e
            IMPORTS["app.models"].trace = traceback.format_exc()
            DB_READY = False

    # Services
    for m in SERVICE_MODULES:
        _import_module(m)

    # Planning
    for m in PLANNING_MODULES:
        _import_module(m)

    critical_failures = [
        r
        for r in IMPORTS.values()
        if (r.name in SERVICE_MODULES or r.name in PLANNING_MODULES) and not r.ok
    ]
    if critical_failures and not MINDGATE_RELAX_IMPORTS:
        SERVICES_READY = False
        return

    # Bind
    try:
        if IMPORTS.get("app.services.generation_service", ImportRecord("")).ok:
            import app.services.generation_service as _gen

            generation_service = _gen
        if IMPORTS.get("app.services.system_service", ImportRecord("")).ok:
            import app.services.system_service as _sys

            system_service = _sys
        if IMPORTS.get("app.services.agent_tools", ImportRecord("")).ok:
            import app.services.agent_tools as _tools

            agent_tools = _tools
        if IMPORTS.get("app.services.master_agent_service", ImportRecord("")).ok:
            import app.services.master_agent_service as _over

            overmind = _over
        if IMPORTS.get("app.overmind.planning.schemas", ImportRecord("")).ok:
            from app.overmind.planning.schemas import MissionPlanSchema as _MPS
            from app.overmind.planning.schemas import PlanWarning as _PW

            MissionPlanSchema, PlanWarning = _MPS, _PW
        if IMPORTS.get("app.overmind.planning.factory", ImportRecord("")).ok:
            import app.overmind.planning.factory as _planning_factory

            planning = _planning_factory
        SERVICES_READY = True
    except Exception as e:
        rec = ImportRecord("binding-phase")
        rec.error = e
        rec.trace = traceback.format_exc()
        IMPORTS["binding-phase"] = rec
        SERVICES_READY = False


def ensure_services(debug: bool = False):
    load_services()
    if SERVICES_READY:
        return
    if debug or MINDGATE_DEBUG:
        _debug_print_imports()
    raise RuntimeError("Core services not loaded. Use: flask mindgate debug-imports --verbose")


def ensure_db():
    load_services()
    if DB_READY:
        return
    raise RuntimeError("Database layer not loaded. Check app.models import failures.")


# ======================================================================================
# UTILITIES
# ======================================================================================
def _safe_json_dump(obj: Any, indent: int = 2) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=indent)
    except Exception:
        return str(obj)


def _print_exception(e: Exception, debug: bool = False):
    C_RED(f"{type(e).__name__}: {e}")
    if debug or MINDGATE_DEBUG:
        C_DIM(traceback.format_exc())


def _get_initiator_user() -> Any:
    user = db.session.get(User, 1)
    if user:
        return user
    user = User.query.first()
    if not user:
        raise RuntimeError("No user found (create at least one User row).")
    return user


def _format_warnings(warnings) -> list[str]:
    result = []
    if not warnings:
        return result
    for w in warnings:
        if PlanWarning and isinstance(w, PlanWarning):
            result.append(
                f"[{w.severity}] {w.code}: {w.message}"
                + (f" (task={w.task_id})" if w.task_id else "")
            )
        else:
            result.append(str(w))
    return result


def print_kv(title: str, data: dict[str, Any]):
    C_YELLOW(f"\n-- {title} --")
    for k, v in data.items():
        click.echo(f"{k}: {v}")


def _planner_default() -> str:
    return DEFAULT_PLANNER_NAME


def _list_available_planners() -> list[str]:
    names: list[str] = []
    try:
        if hasattr(planning, "discover"):
            planning.discover()
        if hasattr(planning, "BasePlanner"):
            bp = planning.BasePlanner
            names = list(bp.available_planners())
        elif hasattr(planning, "get_all_planners"):
            plist = planning.get_all_planners(auto_instantiate=False)
            names = [getattr(p, "name", p.__class__.__name__) for p in plist]
    except Exception:
        pass
    return names


def _dump_plan_json(plan_obj: Any) -> str:
    """
    Safe JSON dump for plan objects across Pydantic versions and fallbacks.
    Removes unsupported ensure_ascii argument for Pydantic v2.
    """
    try:
        # Pydantic v2
        if hasattr(plan_obj, "model_dump_json"):
            return plan_obj.model_dump_json(indent=2)
        # Pydantic v1
        if hasattr(plan_obj, "dict"):
            return json.dumps(plan_obj.dict(), ensure_ascii=False, indent=2)
    except TypeError:
        # Retry with simplest form if indent not supported
        try:
            return plan_obj.model_dump_json()
        except Exception:
            pass
    except Exception:
        pass
    try:
        return json.dumps(plan_obj, ensure_ascii=False, indent=2)
    except Exception:
        try:
            return json.dumps(getattr(plan_obj, "__dict__", {}), ensure_ascii=False, indent=2)
        except Exception:
            return repr(plan_obj)


# ======================================================================================
# DEBUG IMPORTS
# ======================================================================================
@mindgate_cli.cli.command("debug-imports")
@click.option("--verbose", is_flag=True, help="Show tracebacks.")
@click.option("--json-output", "json_out", is_flag=True)
def debug_imports_command(verbose: bool, json_out: bool):
    load_services(force=True)
    data = {n: r.to_dict() for n, r in IMPORTS.items()}
    if json_out:
        click.echo(
            _safe_json_dump(
                {"imports": data, "SERVICES_READY": SERVICES_READY, "DB_READY": DB_READY}
            )
        )
        return
    C_MAGENTA("=== Import Diagnostics ===")
    for n, r in IMPORTS.items():
        status = "OK" if r.ok else "FAIL"
        fn = C_GREEN if r.ok else C_RED
        fn(f"{status:4} {n}")
        if not r.ok:
            C_YELLOW(f"  Error: {r.error}")
            if verbose or MINDGATE_DEBUG:
                C_DIM(r.trace or "")
    C_CYAN(f"\nSERVICES_READY={SERVICES_READY}  DB_READY={DB_READY}")
    if not SERVICES_READY:
        C_YELLOW("\nFix failing modules before using planners / missions.")
        C_DIM("Hints: missing __init__.py, syntax errors, Pydantic mismatch, circular imports.")


# ======================================================================================
# PLANNERS LIST
# ======================================================================================
@mindgate_cli.cli.command("planners")
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--stats", is_flag=True, help="Show factory stats if available.")
def planners_command(json_out: bool, stats: bool):
    try:
        ensure_services()
        names = _list_available_planners()
        payload: dict[str, Any] = {"count": len(names), "planners": names}
        if stats and hasattr(planning, "planner_stats"):
            try:
                payload["stats"] = planning.planner_stats()
            except Exception as e:
                payload["stats_error"] = str(e)
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_CYAN(f"Registered Planners ({len(names)})")
            for n in names:
                click.echo(f"- {n}")
            if stats and "stats" in payload:
                print_kv("Factory Stats", payload["stats"])
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e)}))
        else:
            C_RED("Failed to list planners.")
            _print_exception(e)


# ======================================================================================
# MISSION CREATE
# ======================================================================================
@mindgate_cli.cli.command("mission")
@click.argument("objective", nargs=-1, required=True)
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def mission_command(objective: tuple[str], json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        ensure_db()
        objective_text = " ".join(objective).strip()
        if not objective_text:
            raise ValueError("Objective cannot be empty.")
        user = _get_initiator_user()
        mission = overmind.start_mission(objective=objective_text, initiator=user)
        payload = {
            "mission_id": mission.id,
            "status": getattr(mission.status, "name", str(mission.status)),
            "objective": mission.objective,
        }
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_MAGENTA("=== Overmind Engaged ===")
            C_GREEN(f"Mission #{mission.id} created (status={payload['status']})")
            click.echo(f"Objective: {mission.objective}")
            click.echo(f"Next: flask mindgate mission-status {mission.id}")
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e), "root_causes": _root_cause_summary()}))
        else:
            C_RED("Mission creation failed.")
            _print_exception(e, debug)


# ======================================================================================
# MISSION STATUS
# ======================================================================================
@mindgate_cli.cli.command("mission-status")
@click.argument("mission_id", type=int)
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def mission_status_command(mission_id: int, json_out: bool, debug: bool):
    try:
        ensure_db()
        mission = db.session.get(Mission, mission_id)
        if not mission:
            raise ValueError("Mission not found.")
        tasks = Task.query.filter_by(mission_id=mission.id).all()
        counts: dict[str, int] = {}
        for t in tasks:
            st = getattr(t.status, "name", str(t.status))
            counts[st] = counts.get(st, 0) + 1
        payload = {
            "mission_id": mission.id,
            "status": getattr(mission.status, "name", str(mission.status)),
            "objective": mission.objective,
            "active_plan_id": mission.active_plan_id,
            "task_counts": counts,
        }
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_CYAN(f"Mission #{mission.id} :: {payload['status']}")
            click.echo(f"Objective: {mission.objective}")
            print_kv("Task Counts", counts)
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e)}))
        else:
            C_RED("Failed to fetch mission status.")
            _print_exception(e, debug)


# ======================================================================================
# MISSION TASKS
# ======================================================================================
@mindgate_cli.cli.command("mission-tasks")
@click.argument("mission_id", type=int)
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--limit", type=int, default=200)
@click.option("--debug", is_flag=True)
def mission_tasks_command(mission_id: int, json_out: bool, limit: int, debug: bool):
    try:
        ensure_db()
        mission = db.session.get(Mission, mission_id)
        if not mission:
            raise ValueError("Mission not found.")
        tasks = (
            Task.query.filter_by(mission_id=mission.id).order_by(Task.id.asc()).limit(limit).all()
        )
        rows = []
        for t in tasks:
            rows.append(
                {
                    "id": t.id,
                    "task_key": getattr(t, "task_key", None),
                    "status": getattr(t.status, "name", str(t.status)),
                    "attempts": getattr(t, "attempt_count", None),
                    "max_attempts": getattr(t, "max_attempts", None),
                    "tool_name": getattr(t, "tool_name", None),
                    "priority": getattr(t, "priority", None),
                }
            )
        if json_out:
            click.echo(_safe_json_dump(rows))
        else:
            C_CYAN(f"Mission #{mission.id} Tasks (showing {len(rows)})")
            for r in rows:
                click.echo(
                    f"[{r['status']}] {r['task_key']} (id={r['id']}, attempts={r['attempts']}/{r['max_attempts']}, tool={r['tool_name']})"
                )
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e)}))
        else:
            C_RED("Failed to list mission tasks.")
            _print_exception(e, debug)


# ======================================================================================
# MISSION FOLLOW
# ======================================================================================
@mindgate_cli.cli.command("mission-follow")
@click.argument("mission_id", type=int)
@click.option("--interval", type=float, default=2.5)
@click.option("--timeout", type=int, default=600)
@click.option("--debug", is_flag=True)
def mission_follow_command(mission_id: int, interval: float, timeout: int, debug: bool):
    try:
        ensure_db()
        start = time.time()
        seen_status = None
        C_MAGENTA(f"Following Mission #{mission_id} (interval={interval}s, timeout={timeout}s)")
        while True:
            mission = db.session.get(Mission, mission_id)
            if not mission:
                C_RED("Mission not found.")
                return
            st = getattr(mission.status, "name", str(mission.status))
            if st != seen_status:
                C_CYAN(f"Status: {st}")
                seen_status = st
            if st in ("SUCCESS", "FAILED", "CANCELED"):
                C_GREEN(f"Terminal state: {st}")
                break
            if time.time() - start > timeout:
                C_YELLOW("Timeout reached.")
                break
            time.sleep(interval)
    except Exception as e:
        C_RED("Follow failed.")
        _print_exception(e, debug)


# ======================================================================================
# PLAN (No DB persistence)
# ======================================================================================
@mindgate_cli.cli.command("plan")
@click.argument("objective", nargs=-1, required=True)
@click.option("--planner", "-p", default=lambda: _planner_default(), help="Planner name.")
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def plan_command(objective: tuple[str], planner: str, json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        objective_text = " ".join(objective).strip()
        if not objective_text:
            raise ValueError("Objective cannot be empty.")
        if hasattr(planning, "discover"):
            planning.discover()
        available = _list_available_planners()
        try:
            planner_instance = planning.get_planner(planner)
        except Exception as e:
            suggestion = _maybe_suggest_planner(planner, available)
            msg = f"Planner '{planner}' not found."
            if suggestion:
                msg += f" Did you mean '{suggestion}'?"
            raise RuntimeError(msg) from e

        result = planner_instance.instrumented_generate(objective_text)
        plan_obj = result.plan

        if json_out:
            click.echo(_dump_plan_json(plan_obj))
            return

        C_MAGENTA("=== Plan Result ===")
        click.echo(f"Objective : {objective_text}")
        click.echo(f"Planner   : {result.planner_name} (ver={result.planner_version})")
        click.echo(f"Duration  : {result.duration_seconds:.4f}s")
        click.echo(f"NodeCount : {result.node_count}")
        warn_fmt = _format_warnings(getattr(plan_obj, "warnings", None))
        if warn_fmt:
            C_YELLOW("\nWarnings:")
            for w in warn_fmt:
                click.echo(f"- {w}")
        C_CYAN("\nFull Plan JSON:")
        click.echo(_dump_plan_json(plan_obj))

    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e), "root_causes": _root_cause_summary()}))
        else:
            C_RED("Planning failed.")
            _print_exception(e, debug)


# ======================================================================================
# PLAN MERMAID
# ======================================================================================
@mindgate_cli.cli.command("plan-mermaid")
@click.argument("objective", nargs=-1, required=True)
@click.option("--planner", "-p", default=lambda: _planner_default())
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def plan_mermaid_command(objective: tuple[str], planner: str, json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        obj = " ".join(objective).strip()
        planner_instance = planning.get_planner(planner)
        res = planner_instance.instrumented_generate(obj)
        plan_obj = res.plan
        if not hasattr(plan_obj, "to_mermaid"):
            raise RuntimeError("Plan object lacks to_mermaid()")
        mermaid = plan_obj.to_mermaid()
        payload = {"planner": res.planner_name, "objective": obj, "mermaid": mermaid}
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_CYAN("Mermaid Diagram:")
            click.echo(mermaid)
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e)}))
        else:
            C_RED("plan-mermaid failed.")
            _print_exception(e, debug)


# ======================================================================================
# PLAN DRY
# ======================================================================================
@mindgate_cli.cli.command("plan-dry")
@click.argument("objective", nargs=-1, required=True)
@click.option("--planner", "-p", default=lambda: _planner_default())
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def plan_dry_command(objective: tuple[str], planner: str, json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        obj = " ".join(objective).strip()
        inst = planning.get_planner(planner)
        res = inst.instrumented_generate(obj)
        plan_obj = res.plan
        task_count = None
        if getattr(plan_obj, "stats", None) and "tasks" in plan_obj.stats:
            task_count = plan_obj.stats["tasks"]
        else:
            task_count = len(getattr(plan_obj, "tasks", []))
        payload = {
            "planner": res.planner_name,
            "content_hash": getattr(plan_obj, "content_hash", None),
            "task_count": task_count,
            "warnings": [
                getattr(w, "code", str(w)) for w in getattr(plan_obj, "warnings", []) or []
            ],
        }
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_GREEN("Dry Plan Summary")
            print_kv("Summary", payload)
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e), "root_causes": _root_cause_summary()}))
        else:
            C_RED("Dry plan failed.")
            _print_exception(e, debug)


# ======================================================================================
# PLAN DIFF
# ======================================================================================
@mindgate_cli.cli.command("plan-diff")
@click.argument("plan_a", type=int)
@click.argument("plan_b", type=int)
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def plan_diff_command(plan_a: int, plan_b: int, json_out: bool, debug: bool):
    try:
        ensure_db()
        pa = db.session.get(MissionPlan, plan_a)
        pb = db.session.get(MissionPlan, plan_b)
        if not pa or not pb:
            raise ValueError("One or both plans not found.")
        tasks_a = Task.query.filter_by(plan_id=pa.id).all()
        tasks_b = Task.query.filter_by(plan_id=pb.id).all()
        map_a = {t.task_key: t for t in tasks_a}
        map_b = {t.task_key: t for t in tasks_b}
        added = [k for k in map_b if k not in map_a]
        removed = [k for k in map_a if k not in map_b]
        changed = []
        for k in map_a:
            if k in map_b:
                ta, tb = map_a[k], map_b[k]
                if (ta.description != tb.description) or (ta.tool_name != tb.tool_name):
                    changed.append(k)
        diff_obj = {
            "plan_a": pa.id,
            "plan_b": pb.id,
            "added": added,
            "removed": removed,
            "changed": changed,
        }
        if json_out:
            click.echo(_safe_json_dump(diff_obj))
        else:
            C_CYAN("Plan Diff")
            print_kv(
                "Counts", {"added": len(added), "removed": len(removed), "changed": len(changed)}
            )
            if added:
                C_GREEN("\nAdded:")
                for k in added:
                    click.echo(f"+ {k}")
            if removed:
                C_RED("\nRemoved:")
                for k in removed:
                    click.echo(f"- {k}")
            if changed:
                C_YELLOW("\nChanged:")
                for k in changed:
                    click.echo(f"* {k}")
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e)}))
        else:
            C_RED("Plan diff failed.")
            _print_exception(e, debug)


# ======================================================================================
# REPLAN
# ======================================================================================
@mindgate_cli.cli.command("replan")
@click.argument("mission_id", type=int)
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def replan_command(mission_id: int, json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        ensure_db()
        mission = db.session.get(Mission, mission_id)
        if not mission:
            raise ValueError("Mission not found.")
        state = getattr(mission.status, "name", str(mission.status))
        if state not in ("RUNNING", "FAILED", "PLANNED"):
            raise ValueError(f"Cannot force replan from state {state}")
        mission.status = MissionStatus.ADAPTING
        db.session.commit()
        overmind.run_mission_lifecycle(mission.id)
        payload = {
            "mission_id": mission.id,
            "status": getattr(mission.status, "name", str(mission.status)),
        }
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_GREEN("Adaptive replan triggered.")
            click.echo(f"New status: {payload['status']}")
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e)}))
        else:
            C_RED("Replan command failed.")
            _print_exception(e, debug)


# ======================================================================================
# ASK (Direct LLM)
# ======================================================================================
@mindgate_cli.cli.command("ask")
@click.argument("prompt", nargs=-1, required=True)
@click.option(
    "--mode",
    type=click.Choice(["legacy", "forge", "json", "comprehensive"]),
    default="comprehensive",
    help="LLM mode: legacy | forge | json | comprehensive",
)
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def ask_command(prompt: tuple[str], mode: str, json_out: bool, debug: bool):
    """
    Direct prompt to Maestro LLM gateway (no orchestration).
    Modes:
      legacy -> execute_task_legacy_wrapper({"description": ...})
      forge  -> forge_new_code(prompt=...)
      json   -> generate_json(prompt=...)
    """
    try:
        ensure_services(debug)
        text = " ".join(prompt).strip()
        if not text:
            raise ValueError("Prompt cannot be empty.")
        if not generation_service:
            raise RuntimeError("generation_service module not available.")

        if mode == "legacy":
            if not hasattr(generation_service, "execute_task_legacy_wrapper"):
                raise RuntimeError("Legacy wrapper not available.")
            func = generation_service.execute_task_legacy_wrapper
            result = func({"description": text})
        elif mode == "forge":
            if not hasattr(generation_service, "forge_new_code"):
                raise RuntimeError("forge_new_code not available.")
            result = generation_service.forge_new_code(
                prompt=text, conversation_id=f"ask-{uuid.uuid4()}"
            )
        elif mode == "comprehensive":
            if not hasattr(generation_service, "generate_comprehensive_response"):
                raise RuntimeError("generate_comprehensive_response not available.")
            result = generation_service.generate_comprehensive_response(
                prompt=text, conversation_id=f"ask-{uuid.uuid4()}"
            )
        else:  # json
            if not hasattr(generation_service, "generate_json"):
                raise RuntimeError("generate_json not available.")
            result = generation_service.generate_json(
                prompt=text, conversation_id=f"ask-{uuid.uuid4()}"
            )

        if json_out:
            click.echo(_safe_json_dump(result))
            return

        C_MAGENTA("=== Direct Maestro Response ===")
        status = result.get("status")
        answer = result.get("answer") or result.get("echo") or ""
        if status in ("ok", "success"):
            C_GREEN("\n--- ANSWER ---")
            click.echo(answer or "(empty answer)")
        else:
            C_RED("\n--- ERROR ---")
            click.echo(result.get("error") or result.get("message") or "(unknown error)")

        meta = result.get("meta")
        if meta:
            C_YELLOW("\nMeta:")
            click.echo(_safe_json_dump(meta))
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e), "root_causes": _root_cause_summary()}))
        else:
            C_RED("Ask command failed.")
            _print_exception(e, debug)


# ======================================================================================
# TOOLS
# ======================================================================================
@mindgate_cli.cli.command("tools")
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def tools_command(json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        if not agent_tools:
            raise RuntimeError("agent_tools module not available.")
        index = agent_tools.get_tools_index()
        tools = index.get("tools", [])
        payload = {"version": index.get("version"), "count": len(tools), "tools": tools}
        if json_out:
            click.echo(_safe_json_dump(payload))
        else:
            C_CYAN(f"Tool Arsenal v{payload['version']} (count={payload['count']})")
            for t in tools:
                click.echo(f"- {t}")
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e), "root_causes": _root_cause_summary()}))
        else:
            C_RED("Failed to list tools.")
            _print_exception(e, debug)


# ======================================================================================
# INDEX PROJECT
# ======================================================================================
@mindgate_cli.cli.command("index")
@click.option("--force", is_flag=True, help="Force re-index.")
@click.option("--json-output", "json_out", is_flag=True)
@click.option("--debug", is_flag=True)
def index_command(force: bool, json_out: bool, debug: bool):
    try:
        ensure_services(debug)
        if not system_service:
            raise RuntimeError("system_service module not available.")
        res = system_service.index_project(force=force)
        if getattr(res, "ok", False):
            data = res.data or {}
            payload = {
                "indexed_new": data.get("indexed_new"),
                "total_in_store": data.get("total_in_store"),
                "force": force,
            }
            if json_out:
                click.echo(_safe_json_dump(payload))
            else:
                C_GREEN("Indexing complete.")
                print_kv("Result", payload)
        else:
            err = getattr(res, "error", "Unknown indexing failure.")
            if json_out:
                click.echo(_safe_json_dump({"error": err}))
            else:
                C_RED(f"Indexing failed: {err}")
    except Exception as e:
        if json_out:
            click.echo(_safe_json_dump({"error": str(e), "root_causes": _root_cause_summary()}))
        else:
            C_RED("Index command failed.")
            _print_exception(e, debug)


# ======================================================================================
# REGISTER (Flask app factory hook)
# ======================================================================================
def init_app(app):
    app.cli.add_command(mindgate_cli)


# ======================================================================================
# END OF FILE
# ======================================================================================
