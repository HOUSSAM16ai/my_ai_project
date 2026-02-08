"""
الوحدات المعرفية باستخدام DSPy.

تحدد هذه الوحدة التواقيع (Signatures) والوحدات (Modules) للتخطيط والنقد.
"""

import importlib
import importlib.util
from types import SimpleNamespace


def _dspy_dependencies_available() -> bool:
    """يتحقق من توفر اعتمادات DSPy اللازمة قبل الاستخدام."""

    required_specs = (
        "dspy",
        "litellm",
        "openai",
        "openai.types.beta.threads.message_content",
    )
    for spec in required_specs:
        try:
            if importlib.util.find_spec(spec) is None:
                return False
        except ModuleNotFoundError:
            return False
    return True


def _load_dspy() -> object | None:
    """يحاول تحميل DSPy مع توفير بدائل آمنة عند عدم توفر التبعيات."""

    if not _dspy_dependencies_available():
        return None

    return importlib.import_module("dspy")


_dspy_module = _load_dspy()

if _dspy_module is None:

    class _StubSignature:
        """بديل مبسط لتوقيعات DSPy عند عدم توفر المكتبة."""

    class _StubModule:
        """بديل مبسط لوحدات DSPy عند عدم توفر المكتبة."""

    def _stub_field(*args: object, **kwargs: object) -> None:
        return None

    class _StubChainOfThought:
        """يرفض الاستخدام الفعلي في حال غياب DSPy."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("DSPy غير متاح في بيئة التشغيل الحالية")

    dspy = SimpleNamespace(
        Signature=_StubSignature,
        Module=_StubModule,
        InputField=_stub_field,
        OutputField=_stub_field,
        ChainOfThought=_StubChainOfThought,
    )
else:
    dspy = _dspy_module


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
    """يبني نموذج توليد خطة تعليمية اعتماداً على سياق وهدف محددين."""

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GeneratePlan)

    def forward(self, goal: str, context: list[str]):
        """ينفذ عملية توليد الخطة مع تنسيق السياق كسلسلة نصية."""
        context_str = "\n".join(context) if context else "لا يوجد سياق إضافي."
        return self.generate(goal=goal, context=context_str)


class PlanCritic(dspy.Module):
    """يبني نموذج نقد الخطة لتقييم الجودة وتقديم الملاحظات."""

    def __init__(self):
        super().__init__()
        self.critique = dspy.ChainOfThought(CritiquePlan)

    def forward(self, goal: str, plan_steps: list[str]):
        """ينفذ عملية النقد مع تحويل الخطوات إلى تمثيل نصي."""
        plan_str = "\n".join(str(s) for s in plan_steps)
        return self.critique(goal=goal, plan_steps=plan_str)
