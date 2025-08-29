# -*- coding: utf-8 -*-
# ======================================================================================
# MAESTRO ADAPTER (v1.0 • "BRIDGE-FUSION")
# File: app/services/maestro.py
# ======================================================================================
# PURPOSE:
#   هذا الملف هو "مكيّف" (Adapter) يوفّر الواجهة التي يتوقعها المخطِّط LLMGroundedPlanner
#   أي: module اسمه maestro يحتوي:
#       generation_service.text_completion(...)
#       generation_service.structured_json(...)
#
#   دون الحاجة لإعادة تسمية generation_service.py أو تعديل المخطط.
#
# DESIGN:
#   1. نحاول استيراد module: generation_service.py (كموديول داخلي).
#   2. نفحص إن كان فيه كائن generation_service جاهز ويمتلك الدالتين المطلوبتين:
#        - text_completion
#        - structured_json
#      -> إن نعم: نعيد استعماله كما هو.
#   3. إن لم يكن، ننشئ Adapter ديناميكي:
#        - يستخدم الدوال المتوفرة (text_completion / forge_new_code) إن وجدت.
#        - أو يستدعي LLM مباشرة عبر get_llm_client إن كان متوفراً.
#        - يوفر structured_json بمحاولة استخراج أول {} JSON.
#
#   4. لا نرمي استثناءات قاتلة إلا في حالات استيراد حرجة، ويبقى السلوك مرناً للفشل الآمن.
#
# ENV (اختيارية):
#   MAESTRO_ADAPTER_LOG_LEVEL = DEBUG | INFO | WARNING | ERROR
#   DEFAULT_AI_MODEL (مثلاً: openai/gpt-4o) لو لم يحدد النموذج في الاستدعاء.
#
# SAFE-GUARDS:
#   - إزالة أسوار Markdown (``` ... ```).
#   - استخراج أول كائن JSON متوازن بدل الاعتماد على regex هش.
#   - إعادة المحاولة لعدد محدد (max_retries).
#
# ======================================================================================
from __future__ import annotations

import json
import os
import time
import logging
from typing import Any, Optional, Tuple

# --------------------------------------------------------------------------------------
# Logging Setup (محلي وخفيف)
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("maestro.adapter")
_level = os.getenv("MAESTRO_ADAPTER_LOG_LEVEL", "INFO").upper()
try:
    _LOG.setLevel(getattr(logging, _level, logging.INFO))
except Exception:
    _LOG.setLevel(logging.INFO)
if not _LOG.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][maestro.adapter] %(message)s"))
    _LOG.addHandler(h)

# --------------------------------------------------------------------------------------
# استيراد generation_service الأصلي
# --------------------------------------------------------------------------------------
try:
    from . import generation_service as _gen_mod  # noqa: F401
except Exception as e:
    raise RuntimeError(f"maestro adapter: Cannot import generation_service.py: {e}") from e

# محاولة استيراد عميل الـ LLM (اختياري)
try:
    from .llm_client_service import get_llm_client  # type: ignore
except Exception:
    get_llm_client = None  # type: ignore
    _LOG.warning("llm_client_service.get_llm_client غير متوفر، سيتم الاعتماد على دوال base إن وجدت.")

# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------
def _strip_markdown_fences(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```"):
        # احذف السطر الأول (قد يحتوي label)
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1 :]
        if t.endswith("```"):
            t = t[:-3].strip()
    return t

def _extract_first_json_object(text: str) -> Optional[str]:
    """
    يحاول العثور على أول كائن JSON متوازن { ... } (طريقة قابلة للتوسع).
    """
    if not text:
        return None
    t = _strip_markdown_fences(text)
    start = t.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(t[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return t[start : i + 1]
    return None

def _safe_json_load(payload: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(payload), None
    except Exception as e:
        return None, str(e)

def _default_model() -> str:
    return os.getenv("DEFAULT_AI_MODEL", "openai/gpt-4o")

# --------------------------------------------------------------------------------------
# اختيار أي كائن generation_service موجود في generation_service.py
# --------------------------------------------------------------------------------------
_existing = getattr(_gen_mod, "generation_service", None)

# --------------------------------------------------------------------------------------
# Adapter Class
# --------------------------------------------------------------------------------------
class _GenerationServiceAdapter:
    """
    Adapter يوفر الدوال:
      - text_completion
      - structured_json
    باستراتيجية مرنة:
      1) إذا الكائن الأصلي (_base) يمتلك الدالة المطلوبة نستعملها مباشرة.
      2) وإلا إذا لديه forge_new_code نستعملها لصنع استجابة نصية.
      3) وإلا نحاول استخدام get_llm_client().
    """

    def __init__(self, base: Any = None):
        self._base = base

    # --------------------------- text_completion --------------------------------------
    def text_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
        max_retries: int = 1,
        fail_hard: bool = False,
    ) -> str:
        """
        يعيد نصاً (str) فقط؛ يفشل بصمت ويعيد "" إذا fail_hard=False.
        """
        last_err: Any = None
        for attempt in range(1, max_retries + 2):
            try:
                # (1) دالة أصلية بنفس الاسم
                if self._base and hasattr(self._base, "text_completion"):
                    return self._base.text_completion(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        max_retries=0,
                        fail_hard=fail_hard,
                    )

                # (2) forge_new_code
                if self._base and hasattr(self._base, "forge_new_code"):
                    merged = f"{system_prompt.strip()}\n\nUSER:\n{user_prompt}"
                    resp = self._base.forge_new_code(merged)
                    if isinstance(resp, dict) and resp.get("status") == "success":
                        return (resp.get("answer") or "").strip()
                    last_err = resp.get("error")
                    raise RuntimeError(f"forge_new_code_failed:{last_err}")

                # (3) عميل LLM مباشر
                if get_llm_client:
                    client = get_llm_client()
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                    completion = client.chat.completions.create(
                        model=_default_model(),
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    content = completion.choices[0].message.content or ""
                    return content.strip()

                raise RuntimeError("No underlying LLM interface (base or client) available.")

            except Exception as e:
                last_err = e
                _LOG.warning("text_completion attempt=%d failed: %s", attempt, e)
                time.sleep(0.15)

        if fail_hard:
            raise RuntimeError(f"text_completion_failed:{last_err}")
        return ""

    # --------------------------- structured_json --------------------------------------
    def structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        format_schema: dict,
        temperature: float = 0.2,
        max_retries: int = 1,
        fail_hard: bool = False,
    ) -> Optional[dict]:
        """
        يحاول إنتاج JSON (dict) وفق المتطلبات. يعيد None إذا لم ينجح (ما لم يكن fail_hard=True).
        """
        last_err: Any = None
        required = []
        if isinstance(format_schema, dict):
            required = format_schema.get("required") or []
            if not isinstance(required, list):
                required = []

        # لو الكائن الأصلي لديه structured_json مباشرة نستخدمه:
        if self._base and hasattr(self._base, "structured_json"):
            try:
                return self._base.structured_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    format_schema=format_schema,
                    temperature=temperature,
                    max_retries=max_retries,
                    fail_hard=fail_hard,
                )
            except Exception as e:
                last_err = e
                _LOG.warning("base structured_json failed, falling back: %s", e)

        prompt_sys = (
            f"{system_prompt.strip()}\n"
            "You MUST reply with only one valid JSON object. No markdown fences, no commentary."
        )

        for attempt in range(1, max_retries + 2):
            try:
                raw = self.text_completion(
                    system_prompt=prompt_sys,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=900,
                    max_retries=0,
                    fail_hard=False,
                )
                if not raw:
                    last_err = "empty_response"
                    raise RuntimeError("empty_response")

                candidate = _extract_first_json_object(raw)
                if not candidate:
                    last_err = "no_json_found"
                    raise RuntimeError("no_json_found")

                obj, err = _safe_json_load(candidate)
                if err:
                    last_err = f"json_parse_error:{err}"
                    raise RuntimeError(last_err)

                if not isinstance(obj, dict):
                    last_err = "parsed_not_dict"
                    raise RuntimeError(last_err)

                missing = [k for k in required if k not in obj]
                if missing:
                    last_err = f"missing_required:{missing}"
                    raise RuntimeError(last_err)

                return obj

            except Exception as e:
                _LOG.warning("structured_json attempt=%d failed: %s", attempt, e)
                time.sleep(0.18)

        if fail_hard:
            raise RuntimeError(f"structured_json_failed:{last_err}")
        return None


# --------------------------------------------------------------------------------------
# اختيار ما سنصدّره:
#   - إذا _existing موجود ويمتلك الدالتين المطلوبتين => استعماله مباشرة.
#   - غير ذلك: إنشاء Adapter ولفّ الكائن الأصلي (قد يكون None).
# --------------------------------------------------------------------------------------
if _existing and all(hasattr(_existing, m) for m in ("text_completion", "structured_json")):
    generation_service = _existing
    _LOG.info("Using existing generation_service (already provides required methods).")
else:
    generation_service = _GenerationServiceAdapter(_existing)
    if _existing:
        _LOG.info("Wrapped existing generation_service with adapter (added missing methods).")
    else:
        _LOG.info("Created pure adapter (no original generation_service object present).")

__all__ = ["generation_service"]
# ======================================================================================
# END OF FILE
# ======================================================================================