from __future__ import annotations

from contextlib import contextmanager
from types import ModuleType, SimpleNamespace
import importlib
import importlib.util
import sys

def _build_dspy_stub() -> ModuleType:
    """ينشئ وحدة بديلة لـ DSPy لتوفير واجهة خفيفة عند غياب الاعتماد."""
    module = ModuleType("dspy")

    class Signature:
        """يمثل توقيعاً مجرداً للمهام الاستدلالية."""

    class InputField:
        """يصف حقلاً إدخالياً مع وصف عربي مبسط."""

        def __init__(self, desc: str) -> None:
            self.desc = desc

    class OutputField:
        """يصف حقلاً إخراجياً مع وصف عربي مبسط."""

        def __init__(self, desc: str) -> None:
            self.desc = desc

    class Module:
        """واجهة مبسطة للوحدات القابلة للتنفيذ."""

        def __call__(self, **kwargs: str) -> SimpleNamespace:
            return SimpleNamespace(refined_query=kwargs.get("user_query", ""))

    class ChainOfThought:
        """تنفيذ مبسط لسلسلة تفكير تعتمد على التوقيع."""

        def __init__(self, signature: type[Signature]) -> None:
            self.signature = signature

        def __call__(self, **kwargs: str) -> SimpleNamespace:
            return SimpleNamespace(refined_query=kwargs.get("user_query", ""))

    class LM:
        """نموذج لغة افتراضي لتوفير واجهة متوافقة مع الاختبارات."""

        def __init__(self, model: str, api_key: str, api_base: str, max_tokens: int) -> None:
            self.model = model
            self.api_key = api_key
            self.api_base = api_base
            self.max_tokens = max_tokens

    def configure(*_args: object, **_kwargs: object) -> None:
        return None

    @contextmanager
    def context(**_kwargs: object):
        yield

    module.Signature = Signature
    module.InputField = InputField
    module.OutputField = OutputField
    module.Module = Module
    module.ChainOfThought = ChainOfThought
    module.LM = LM
    module.configure = configure
    module.context = context
    return module


def _ensure_dspy_module() -> ModuleType:
    """يضمن توفير وحدة DSPy الحقيقية أو البديلة حسب البيئة."""
    if "dspy" in sys.modules:
        return sys.modules["dspy"]
    spec = importlib.util.find_spec("dspy")
    if spec is None:
        module = _build_dspy_stub()
        sys.modules["dspy"] = module
        return module
    module = importlib.import_module("dspy")
    sys.modules["dspy"] = module
    return module


dspy = _ensure_dspy_module()

class QueryRefinementSignature(dspy.Signature):
    """يحول الاستعلام التعليمي إلى صياغة دلالية دقيقة قابلة للبحث."""
    user_query = dspy.InputField(desc="The raw query from the student.")
    refined_query = dspy.OutputField(desc="The optimized query for vector search, emphasizing exam year, subject, and exercise number.")

class QueryRefiner(dspy.Module):
    """يبني سلسلة تفكير لإعادة صياغة الاستعلامات التعليمية."""
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(QueryRefinementSignature)

    def forward(self, user_query: str):
        return self.prog(user_query=user_query)

def get_refined_query(user_query: str, api_key: str, model_name: str = "mistralai/devstral-2512:free") -> str:
    """ينفذ تنقيح الاستعلام باستخدام DSPy مع استراتيجية تراجع عند الفشل."""
    try:
        # In DSPy 3.x, use dspy.LM
        # We point to OpenRouter using 'openai/' prefix and custom base
        lm = dspy.LM(
            model=f"openai/{model_name}",
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            max_tokens=200
        )

        # Use context manager for thread safety
        with dspy.context(lm=lm):
            refiner = QueryRefiner()
            result = refiner(user_query=user_query)
            return result.refined_query

    except Exception as e:
        # Fallback if DSPy fails (e.g. network, auth)
        print(f"DSPy refinement failed: {e}")
        return user_query
