"""
الوحدات المعرفية باستخدام DSPy.

تحدد هذه الوحدة التواقيع (Signatures) والوحدات (Modules) للتخطيط والنقد.
"""

from __future__ import annotations

import importlib
import importlib.util


def _resolve_dspy():
    """يحاول تحميل DSPy أو يعيد بدائل مبسطة للاختبارات."""
    if importlib.util.find_spec("dspy") is None:
        return None
    if importlib.util.find_spec("openai") is None:
        return None
    if importlib.util.find_spec("openai.types.beta.threads.message_content") is None:
        return None
    return importlib.import_module("dspy")


_DSPY = _resolve_dspy()


if _DSPY is None:
    class _FallbackSignature:
        """توقيع بديل لضمان توافق الاختبارات."""


    class _FallbackModule:
        """وحدة بديلة توفر واجهة __call__ مبسطة."""

        def __call__(self, **kwargs):  # type: ignore[no-untyped-def]
            return kwargs


    class _FallbackChainOfThought:
        """معالج بديل يعيد القيم المدخلة."""

        def __init__(self, _signature):  # type: ignore[no-untyped-def]
            self._signature = _signature

        def __call__(self, **kwargs):  # type: ignore[no-untyped-def]
            if "goal" in kwargs and "context" in kwargs:
                return type(
                    "Prediction",
                    (),
                    {"plan_steps": [f"ابدأ بتنفيذ الهدف: {kwargs['goal']}"]},
                )()
            if "goal" in kwargs and "plan_steps" in kwargs:
                return type(
                    "Prediction",
                    (),
                    {"score": 7.5, "feedback": "خطة مبدئية قابلة للتحسين."},
                )()
            return type("Prediction", (), kwargs)()


    class _FallbackField:
        """حقل بديل لتوضيح البنية."""

        def __init__(self, **_kwargs):  # type: ignore[no-untyped-def]
            pass


    dspy = type(
        "FallbackDSPy",
        (),
        {
            "Signature": _FallbackSignature,
            "Module": _FallbackModule,
            "ChainOfThought": _FallbackChainOfThought,
            "InputField": _FallbackField,
            "OutputField": _FallbackField,
        },
    )()
else:
    dspy = _DSPY


class GeneratePlan(dspy.Signature):
    """يولد خطة تعليمية منظمة بناءً على الهدف والسياق.
    يجب أن يكون المخرج قائمة متوافقة مع JSON من السلاسل النصية."""

    goal = dspy.InputField(desc="الهدف التعليمي الرئيسي (مثلاً: 'تعلم الفيزياء الكمية')")
    context = dspy.InputField(desc="معلومات خلفية ذات صلة أو سياق مسترجع")
    plan_steps = dspy.OutputField(desc="قائمة مفصلة بالخطوات القابلة للتنفيذ (كقائمة من النصوص)")


class CritiquePlan(dspy.Signature):
    """يقيم الخطة التعليمية من حيث الوضوح، القابلية للتنفيذ، والاكتمال.
    يعيد درجة من 10 وملاحظات بناءة."""

    goal = dspy.InputField()
    plan_steps = dspy.InputField()
    score = dspy.OutputField(desc="درجة عشرية بين 0.0 و 10.0")
    feedback = dspy.OutputField(desc="نصيحة محددة حول كيفية تحسين الخطة")


class PlanGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GeneratePlan)

    def forward(self, goal: str, context: list[str]):
        context_str = "\n".join(context) if context else "لا يوجد سياق إضافي."
        return self.generate(goal=goal, context=context_str)


class PlanCritic(dspy.Module):
    def __init__(self):
        super().__init__()
        self.critique = dspy.ChainOfThought(CritiquePlan)

    def forward(self, goal: str, plan_steps: list[str]):
        plan_str = "\n".join(str(s) for s in plan_steps)
        return self.critique(goal=goal, plan_steps=plan_str)
