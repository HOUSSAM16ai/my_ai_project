"""
الوحدات المعرفية باستخدام DSPy.

تحدد هذه الوحدة التواقيع (Signatures) والوحدات (Modules) للتخطيط والنقد.
"""

import dspy


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
