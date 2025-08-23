# app/cli/mindgate_commands.py - v100.1 "MindGate Hyper-Conduit (Blueprint Edition)"
from __future__ import annotations
import uuid, json, time
from typing import List, Optional
import click
from flask import Blueprint, current_app

mindgate_cli = Blueprint("mindgate", __name__, cli_group="mindgate")

# محاولات استيراد هادئة
try:
    from app.services import generation_service, system_service, agent_tools
except Exception:
    generation_service = None
    system_service = None
    agent_tools = None

try:
    from app import db
    from app.models import Message
except Exception:
    db = None
    Message = None

# ألوان
C_MAGENTA = lambda s: click.secho(s, fg="magenta")
C_CYAN    = lambda s: click.secho(s, fg="cyan")
C_GREEN   = lambda s: click.secho(s, fg="green")
C_RED     = lambda s: click.secho(s, fg="red")
C_YELLOW  = lambda s: click.secho(s, fg="yellow")
C_DIM     = lambda s: click.secho(s, fg="white", dim=True)

# ---------------- Utilities ----------------
def _gen_conversation_id(): return str(uuid.uuid4())

def _safe_json(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

def _persist(conv_id: str, role: str, content: str):
    if not (db and Message):
        return
    try:
        m = Message(conversation_id=conv_id, role=role, content=content)
        db.session.add(m); db.session.commit()
    except Exception:
        db.session.rollback()

def _history(conv_id: str, limit: int = 30) -> List[dict]:
    if not (db and Message):
        return []
    try:
        rows = (db.session.query(Message)
                .filter(Message.conversation_id == conv_id)
                .order_by(Message.id.desc())
                .limit(limit)
                .all())
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]
    except Exception:
        return []

def _render_telemetry(result: dict):
    telemetry = (result or {}).get("telemetry")
    if not telemetry:
        return
    click.secho("\n--- TELEMETRY ---", fg="yellow")
    for k in ["finalization_reason", "steps_taken", "tools_invoked",
              "distinct_tools", "compression_events", "error"]:
        if k in telemetry:
            click.echo(f"  {k}: {telemetry.get(k)}")

# ---------------- ask (Orchestrator) ----------------
@mindgate_cli.cli.command("ask")
@click.argument("prompt", nargs=-1, required=True)
@click.option("--conv-id", "-c", help="معرّف محادثة موجود.")
@click.option("--json-out", is_flag=True, help="طباعة خام JSON.")
@click.option("--export", help="تصدير النتيجة إلى ملف.")
@click.option("--max-steps", type=int, help="تجاوز عدد الخطوات الافتراضي.")
def ask_command(prompt, conv_id, json_out, export, max_steps):
    if generation_service is None:
        C_RED("generation_service غير متوفر. تحقق من تثبيت الحزمة/المسار.")
        return
    text = " ".join(prompt).strip()
    if not text:
        C_RED("نص فارغ.")
        return

    conversation_id = conv_id or _gen_conversation_id()
    C_MAGENTA("=== MindGate Orchestrator ===")
    click.echo(f"Conversation: {conversation_id}")
    click.echo(f"Prompt: {text[:120]}")

    if max_steps:
        current_app.config["AGENT_MAX_STEPS"] = max_steps

    hist = _history(conversation_id) if conv_id else []
    t0 = time.time()
    try:
        result = generation_service.forge_new_code(
            prompt=text,
            conversation_history=hist,
            conversation_id=conversation_id
        )
    except Exception as e:
        C_RED(f"فشل استدعاء orchestrator: {e}")
        return
    elapsed = round((time.time() - t0) * 1000, 2)
    status = result.get("status")

    if json_out:
        click.echo(_safe_json(result))
    else:
        if status == "success":
            C_GREEN("\n--- ANSWER ---")
            click.echo(result.get("answer", "(no answer)"))
        elif status == "partial":
            C_YELLOW("\n--- PARTIAL ---")
            click.echo(result.get("message"))
            if "answer" in result:
                click.echo(result["answer"])
        else:
            C_RED("\n--- ERROR ---")
            click.echo(result.get("message"))
            if "trace" in result:
                C_DIM(result["trace"])
        _render_telemetry(result)
        click.echo(f"\nElapsed: {elapsed} ms")

    if export:
        try:
            with open(export, "w", encoding="utf-8") as f:
                f.write(_safe_json(result))
            C_GREEN(f"Exported → {export}")
        except Exception as e:
            C_RED(f"فشل التصدير: {e}")

    if not conv_id:
        C_DIM(f"لاستكمال المحادثة: --conv-id {conversation_id}")

# ---------------- chat (تفاعلي مباشر) ----------------
@mindgate_cli.cli.command("chat")
@click.option("--model", default="openai/gpt-4o-mini", help="معرّف النموذج (OpenRouter).")
@click.option("--conv-id", "-c", help="استمرار محادثة.")
@click.option("--stream", is_flag=True, help="بث تجريبي.")
@click.option("--timeout", type=float, default=180.0, help="زمن انتظار (ث).")
def chat_command(model, conv_id, stream, timeout):
    try:
        import openai
    except Exception:
        C_RED("مكتبة openai غير مثبتة. ثبّت: pip install openai")
        return

    api_key = current_app.config.get("OPENROUTER_API_KEY")
    if not api_key:
        C_RED("OPENROUTER_API_KEY مفقود في الإعدادات.")
        return

    try:
        client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    except Exception as e:
        C_RED(f"تهيئة العميل فشلت: {e}")
        return

    conversation_id = conv_id or _gen_conversation_id()
    C_MAGENTA("=== Interactive Chat ===")
    click.echo(f"Conversation: {conversation_id}")
    click.echo(f"Model: {model}")
    click.echo("اكتب exit أو quit للخروج.")
    click.echo("-" * 40)

    hist = _history(conversation_id) if conv_id else []
    while True:
        user_in = click.prompt("You", prompt_suffix="> ")
        if user_in.lower().strip() in ("exit", "quit"):
            break
        if not user_in.strip():
            continue
        hist.append({"role": "user", "content": user_in})
        _persist(conversation_id, "user", user_in)
        click.secho("AI thinking...", fg="cyan")
        try:
            if not stream:
                completion = client.chat.completions.create(
                    model=model,
                    messages=hist,
                    timeout=timeout
                )
                ans = completion.choices[0].message.content
                hist.append({"role": "assistant", "content": ans})
                _persist(conversation_id, "assistant", ans)
                click.secho(f"AI: {ans}", fg="green")
            else:
                stream_resp = client.chat.completions.create(
                    model=model,
                    messages=hist,
                    stream=True,
                )
                parts = []
                click.secho("AI: ", fg="green", nl=False)
                for chunk in stream_resp:
                    try:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            parts.append(delta)
                            click.echo(delta, nl=False)
                    except Exception:
                        pass
                click.echo()
                final = "".join(parts).strip()
                if final:
                    hist.append({"role": "assistant", "content": final})
                    _persist(conversation_id, "assistant", final)
        except openai.APITimeoutError:
            C_YELLOW("Timeout.")
        except Exception as e:
            C_RED(f"Error: {e}")

    C_MAGENTA("--- Chat Closed ---")
    if not conv_id:
        C_DIM(f"للمتابعة لاحقاً: --conv-id {conversation_id}")

# ---------------- index ----------------
@mindgate_cli.cli.command("index")
@click.option("--force", is_flag=True, help="إعادة فهرسة قسرية.")
@click.option("--no-chunk", is_flag=True, help="تعطيل التقسيم.")
def index_command(force, no_chunk):
    if not system_service:
        C_RED("system_service غير متوفر.")
        return
    C_CYAN("Indexing project...")
    res = system_service.index_project(force=force, chunking=not no_chunk)
    if res.ok:
        data = res.data or {}
        click.secho("Index Result:", fg="yellow", bold=True)
        for k in ["indexed_new", "total_in_store", "chunking", "force"]:
            click.secho(f"  {k}: ", fg="cyan", nl=False); click.echo(data.get(k))
    else:
        C_RED(f"Index Failed: {res.error}")

# ---------------- context ----------------
@mindgate_cli.cli.command("context")
@click.argument("query")
@click.option("--limit", default=5)
def context_command(query, limit):
    if not system_service:
        C_RED("system_service غير متوفر.")
        return
    res = system_service.find_related_context(query, limit=limit)
    if not res.ok:
        C_RED(f"Context Failed: {res.error}")
        return
    rows = (res.data or {}).get("results", [])
    C_CYAN(f"Top {len(rows)} results:")
    for r in rows:
        p = r.get("file_path")
        s = r.get("hybrid_score")
        t = r.get("priority_tier")
        pv = r.get("preview", "").replace("\n", " ")[:85]
        click.echo(f"- {p} | score={s:.4f} | tier={t} | {pv}...")

# ---------------- tools ----------------
@mindgate_cli.cli.command("tools")
def tools_command():
    if not agent_tools:
        C_RED("agent_tools غير متوفر.")
        return
    try:
        schema = agent_tools.get_tools_schema()
    except Exception as e:
        C_RED(f"فشل جلب الأدوات: {e}")
        return
    C_CYAN(f"Total Tools: {len(schema)}")
    for t in schema:
        fn = t.get("function", {})
        click.echo(f" - {fn.get('name')}: {fn.get('description', '(no description)')}")

# ---------------- diagnose ----------------
@mindgate_cli.cli.command("diagnose")
def diagnose_command():
    C_MAGENTA("=== Diagnostics ===")
    orch_ver = getattr(generation_service, "__version__", "N/A") if generation_service else "N/A"
    sys_ok = False
    if system_service:
        diag = system_service.diagnostics()
        if diag.ok:
            data = diag.data or {}
            click.secho("\nSystemService:", fg="yellow", bold=True)
            for k in ["version", "embedding_model_loaded", "cache_enabled", "cache_size", "allowed_ext_count"]:
                click.secho(f"  {k}: ", fg="cyan", nl=False); click.echo(data.get(k))
            sys_ok = True
        else:
            C_RED("Diagnostics call failed in system_service.")
    click.secho("\nOrchestrator:", fg="yellow", bold=True)
    for k, v in {
        "version": orch_ver,
        "loaded": bool(generation_service),
        "system_service_ok": sys_ok
    }.items():
        click.secho(f"  {k}: ", fg="cyan", nl=False); click.echo(v)
    db_status = "available" if (db and Message) else "unavailable"
    click.secho("\nDatabase:", fg="yellow", bold=True)
    click.secho("  message_table: ", fg="cyan", nl=False); click.echo(db_status)
    C_DIM("\nأضف لاحقاً: summarize / plan / critic.")