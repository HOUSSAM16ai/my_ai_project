# ======================================================================================
#  MAESTRO ADAPTER (v2.5.0 • "BRIDGE-FUSION-OMNI")
#  File: app/services/maestro.py
# ======================================================================================
#  PURPOSE:
#    هذا الملف يعمل كطبقة توافق (Adapter / Bridge) بين أي مكوّن (مثل المخطط LLMGroundedPlanner،
#    أو الخدمات الأخرى) وبين خدمة التوليد المركزية generation_service الحقيقية الموجودة في
#    generation_service.py. الهدف:
#       - توفير واجهة موحّدة: maestro.generation_service.text_completion(...)
#                                   maestro.generation_service.structured_json(...)
#       - ضمان استمرار العمل حتى لو كان generation_service جزئياً أو غير موجود (Fallback).
#       - تقديم تشخيص (Diagnostics) واضح وسجلات (Logging) مُهيكلة.
#
#  DESIGN OVERVIEW:
#    1) نحاول استيراد module (generation_service.py).
#       - إذا وجدنا كائناً باسم generation_service يوفّر الدالتين (text_completion, structured_json)
#         نستعمله مباشرة (Pass-Through Mode).
#    2) إذا الكائن مفقود أو تنقصه الدوال: ننشئ Adapter ديناميكي (_GenerationServiceAdapter) يلتف
#       حول الكائن الأصلي (إن وُجد) ويزوّد الدوال المفقودة بمنطق احتياطي.
#    3) إذا لم يوجد كائن إطلاقاً نستعمل Pure Adapter مع:
#         - استخدام forge_new_code إن توفّر.
#         - أو استدعاء مباشر لعميل الـ LLM get_llm_client() (إن وُجد).
#         - أو إرجاع استجابات فارغة آمنة بدلاً من تحطيم النظام.
#    4) structured_json في وضع fallback تُجرّب استخراج أوّل كائن JSON متوازن {} مع إعادة المحاولة.
#
#  SAFETY / RELIABILITY:
#    - لا تُرمى استثناءات قاتلة أثناء إنشاء الـ adapter (إلا عند فشل استيراد generation_service نفسه).
#    - إعادة المحاولة الخفيفة (retry) مع Backoff ثابت صغير.
#    - إزالة أسوار Markdown والتحقق من توازن الأقواس.
#    - حفظ وصف آخر خطأ في diagnostics().
#    - دعم تحديد النموذج عبر: param > MAESTRO_FORCE_MODEL > AI_MODEL_OVERRIDE > DEFAULT_AI_MODEL > fallback.
#
#  ENV VARS (اختيارية):
#       MAESTRO_ADAPTER_LOG_LEVEL    (افتراضي INFO)
#       DEFAULT_AI_MODEL             (مثال: openai/gpt-4o-mini)
#       AI_MODEL_OVERRIDE
#       MAESTRO_FORCE_MODEL
#       MAESTRO_ADAPTER_MAX_RETRIES  (افتراضي 1)
#       MAESTRO_ADAPTER_JSON_MAX_RETRIES (افتراضي 1)
#
#  PUBLIC EXPORTS:
#       generation_service   -> الكائن الذي يملك text_completion / structured_json
#       diagnostics()        -> معلومات حالة وتشخيص
#       ensure_adapter_ready() -> للتحقق السريع برمجياً
#
#  VERSION COMPAT NOTE:
#       متوافق مع الإصدار المعزّز generation_service v17 وما بعده، ويظل آمناً إن كان الإصدار أقدم.
#
# ======================================================================================
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

# Text processing utilities (shared across services)
from app.utils.text_processing import extract_first_json_object as _extract_first_json_object

__version__ = "2.5.0"

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("maestro.adapter")
_level = os.getenv("MAESTRO_ADAPTER_LOG_LEVEL", "INFO").upper()
try:
    _LOG.setLevel(getattr(logging, _level, logging.INFO))
except Exception:
    _LOG.setLevel(logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][maestro.adapter] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Try import generation_service module
# --------------------------------------------------------------------------------------
try:
    from . import generation_service as _gen_mod
except Exception as e:
    # هذه حالة حرجة لأن معظم النظام يعتمد على وجود الملف. نرفع استثناء صريح مبكر.
    raise RuntimeError(f"[maestro.adapter] Cannot import generation_service.py: {e}") from e

# --------------------------------------------------------------------------------------
# Optional direct LLM client (fallback path)
# --------------------------------------------------------------------------------------
try:
    from .llm_client_service import get_llm_client
except Exception:
    get_llm_client = None
    _LOG.warning("llm_client_service.get_llm_client غير متوفر، سيُستخدم مسار fallback فقط إن لزم.")

# --------------------------------------------------------------------------------------
# State for diagnostics
# --------------------------------------------------------------------------------------
_LAST_ERRORS: dict[str, str] = {}
_ADAPTER_MODE: str = "unknown"  # "pass_through" | "wrapped" | "pure"
_BASE_OBJ_TYPE: str = "none"
_CREATION_TS = time.time()


# ======================================================================================
# Utility Functions
# ======================================================================================
# NOTE: _strip_markdown_fences and _extract_first_json_object are now imported from
# app.utils.text_processing to eliminate code duplication across services.


def _safe_json_load(payload: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(payload), None
    except Exception as e:
        return None, str(e)


def _select_model(explicit: str | None = None) -> str:
    """
    Priority: explicit > MAESTRO_FORCE_MODEL > AI_MODEL_OVERRIDE > DEFAULT_AI_MODEL > fallback
    """
    if explicit and explicit.strip():
        return explicit.strip()
    force = os.getenv("MAESTRO_FORCE_MODEL")
    if force and force.strip():
        return force.strip()
    override = os.getenv("AI_MODEL_OVERRIDE")
    if override and override.strip():
        return override.strip()
    default_m = os.getenv("DEFAULT_AI_MODEL", "").strip()
    if default_m:
        return default_m
    return "openai/gpt-4o"


def _int_env(name: str, default: int) -> int:
    try:
        raw = os.getenv(name)
        if raw is None:
            return default
        return int(raw)
    except Exception:
        return default


# ======================================================================================
# Attempt to fetch existing generation_service object
# ======================================================================================
_existing = getattr(_gen_mod, "generation_service", None)
if _existing is not None:
    _BASE_OBJ_TYPE = f"{type(_existing).__name__}"


# ======================================================================================
# Adapter Class
# ======================================================================================
class _GenerationServiceAdapter:
    """
    Adapter يوفر:
      - text_completion
      - structured_json

    STRATEGY:
      1) إذا base لديه الدالة -> استدعاء مباشر.
      2) إذا لا، محاولة استخدام forge_new_code للنص.
      3) آخر شيء: LLM client مباشر (إن توفّر) أو فشل آمن يعيد "" / None.
    """

    def __init__(self, base: Any = None):
        self._base = base
        self._text_retries = _int_env("MAESTRO_ADAPTER_MAX_RETRIES", 1)
        self._json_retries = _int_env("MAESTRO_ADAPTER_JSON_MAX_RETRIES", 1)

    # --------------------------- text_completion --------------------------------------
    def text_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
        max_retries: int | None = None,
        fail_hard: bool = False,
        model: str | None = None,
    ) -> str:
        """
        Returns plain string. If fail_hard=False returns "" on failure.
        """
        attempts = self._text_retries if max_retries is None else max_retries
        model_name = _select_model(model)
        last_err: Any = None

        for attempt in range(1, attempts + 2):
            try:
                # 1) Base direct
                if self._base and hasattr(self._base, "text_completion"):
                    return self._base.text_completion(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        max_retries=0,
                        fail_hard=fail_hard,
                        model=model_name,
                    )

                # 2) forge_new_code path
                if self._base and hasattr(self._base, "forge_new_code"):
                    merged = f"{system_prompt.strip()}\n\nUSER:\n{user_prompt}"
                    resp = self._base.forge_new_code(merged, model=model_name)
                    if isinstance(resp, dict) and resp.get("status") == "success":
                        return (resp.get("answer") or "").strip()
                    last_err = resp.get("error") if isinstance(resp, dict) else "forge_failure"
                    raise RuntimeError(f"forge_new_code_failed:{last_err}")

                # 3) Direct LLM
                if get_llm_client:
                    client = get_llm_client()
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    content = completion.choices[0].message.content or ""
                    return content.strip()

                raise RuntimeError("No underlying generation method available.")

            except Exception as e:
                last_err = e
                _LAST_ERRORS["text_completion"] = str(e)
                _LOG.warning(
                    "text_completion attempt=%d (limit=%d) failed: %s", attempt, attempts + 1, e
                )
                if attempt <= attempts:
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
        max_retries: int | None = None,
        fail_hard: bool = False,
        model: str | None = None,
    ) -> dict | None:
        """
        Returns dict or None (unless fail_hard=True).
        """
        attempts = self._json_retries if max_retries is None else max_retries
        required = []
        if isinstance(format_schema, dict):
            req = format_schema.get("required")
            if isinstance(req, list):
                required = req

        # Try direct if base provides structured_json:
        if self._base and hasattr(self._base, "structured_json"):
            try:
                return self._base.structured_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    format_schema=format_schema,
                    temperature=temperature,
                    max_retries=attempts,
                    fail_hard=fail_hard,
                    model=model,
                )
            except Exception as e:
                _LAST_ERRORS["structured_json_direct"] = str(e)
                _LOG.warning("Direct base structured_json failed -> fallback. Error: %s", e)

        sys = (
            system_prompt.strip()
            + "\nYou MUST output ONLY one valid JSON object. No markdown fences. No commentary."
        )
        last_err: Any = None

        for attempt in range(1, attempts + 2):
            try:
                raw = self.text_completion(
                    system_prompt=sys,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=900,
                    max_retries=0,
                    fail_hard=False,
                    model=model,
                )
                if not raw:
                    last_err = "empty_response"
                    raise RuntimeError(last_err)

                candidate = _extract_first_json_object(raw)
                if not candidate:
                    last_err = "no_json_found"
                    raise RuntimeError(last_err)

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
                _LAST_ERRORS["structured_json"] = str(e)
                _LOG.warning(
                    "structured_json attempt=%d (limit=%d) failed: %s", attempt, attempts + 1, e
                )
                if attempt <= attempts:
                    time.sleep(0.18)

        if fail_hard:
            raise RuntimeError(f"structured_json_failed:{last_err}")
        return None


# ======================================================================================
# Choose export strategy
# ======================================================================================
if _existing and all(hasattr(_existing, m) for m in ("text_completion", "structured_json")):
    generation_service = _existing
    _ADAPTER_MODE = "pass_through"
    _LOG.info("Using existing generation_service (full feature / pass-through).")
elif _existing:
    generation_service = _GenerationServiceAdapter(_existing)
    _ADAPTER_MODE = "wrapped"
    _LOG.info("Wrapped existing generation_service (added missing methods).")
else:
    generation_service = _GenerationServiceAdapter(None)
    _ADAPTER_MODE = "pure"
    _LOG.warning("Created pure adapter (no original generation_service object present).")


# ======================================================================================
# Diagnostics / API
# ======================================================================================
def diagnostics() -> dict:
    """
    Returns adapter status & internal flags (does NOT call external network).
    """
    return {
        "adapter_version": __version__,
        "mode": _ADAPTER_MODE,
        "base_object_type": _BASE_OBJ_TYPE,
        "has_generation_service_attr": _existing is not None,
        "pass_through": _ADAPTER_MODE == "pass_through",
        "default_model_env": os.getenv("DEFAULT_AI_MODEL"),
        "force_model_env": os.getenv("MAESTRO_FORCE_MODEL"),
        "override_model_env": os.getenv("AI_MODEL_OVERRIDE"),
        "selected_default_model_now": _select_model(),
        "creation_epoch": _CREATION_TS,
        "last_errors": dict(_LAST_ERRORS),
    }


def ensure_adapter_ready(raise_on_fail: bool = False) -> bool:
    """
    Quick readiness probe: returns True if generation_service exposes the required interface.
    """
    ok = all(hasattr(generation_service, m) for m in ("text_completion", "structured_json"))
    if not ok and raise_on_fail:
        raise RuntimeError("Maestro adapter is not ready: missing required methods.")
    return ok


__all__ = [
    "__version__",
    "diagnostics",
    "ensure_adapter_ready",
    "generation_service",
]

# ======================================================================================
# Self-Test (manual execution)
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    print("=== maestro.adapter diagnostics ===")
    print(json.dumps(diagnostics(), ensure_ascii=False, indent=2))
    ready = ensure_adapter_ready()
    print("READY:", ready)
    if ready:
        try:
            txt = generation_service.text_completion(
                "You are tester", "Say ONLY OK.", temperature=0.0, max_retries=0
            )
            print("text_completion =>", txt)
            js = generation_service.structured_json(
                "System",
                'Return {"answer":"OK"}',
                {
                    "type": "object",
                    "properties": {"answer": {"type": "string"}},
                    "required": ["answer"],
                },
                temperature=0.0,
                max_retries=0,
            )
            print("structured_json =>", js)
        except Exception as e:
            print("Self-test error:", e)
# ======================================================================================
# END OF FILE
# ======================================================================================
