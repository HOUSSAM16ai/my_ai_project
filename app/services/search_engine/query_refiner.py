import dspy

from app.core.logging import get_logger
from app.core.types import JSONValue

logger = get_logger(__name__)


class StructuredQuerySignature(dspy.Signature):
    """
    يحلل الاستعلام التعليمي لاستخراج البيانات الوصفية وبناء عبارة بحث منقحة.

    يركز على استخراج:
    - السنة: سنة الامتحان عند ذكرها.
    - المادة: اسم المادة الدراسية.
    - الشعبة: الشعبة الأكاديمية.
    - عبارة البحث المنقحة: ترجمة موجزة للموضوع للاستخدام في البحث الدلالي.
    """

    user_query: str = dspy.InputField(desc="The raw query from the student.")
    refined_query: str = dspy.OutputField(desc="The optimized search term.")
    year: int | None = dspy.OutputField(desc="The exam year if mentioned, else None.")
    subject: str | None = dspy.OutputField(desc="The subject name if mentioned, else None.")
    branch: str | None = dspy.OutputField(desc="The branch name if mentioned, else None.")


class StructuredQueryRefiner(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(StructuredQuerySignature)

    def forward(self, user_query: str):
        return self.prog(user_query=user_query)


def get_refined_query(
    user_query: str, api_key: str, model_name: str = "mistralai/devstral-2512:free"
) -> dict[str, str | int | None]:
    """
    يستخدم DSPy لتنقية الاستعلام واستخراج البيانات الوصفية ذات الصلة.

    يعيد قاموساً يحتوي على مفاتيح: refined_query، year، subject، branch.
    """
    try:
        lm = dspy.LM(
            model=f"openai/{model_name}",
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            max_tokens=300,
        )

        with dspy.context(lm=lm):
            refiner = StructuredQueryRefiner()
            result = refiner(user_query=user_query)

            # Extract and clean
            return {
                "refined_query": result.refined_query,
                "year": _safe_int(result.year),
                "subject": result.subject
                if result.subject and result.subject.lower() != "none"
                else None,
                "branch": result.branch
                if result.branch and result.branch.lower() != "none"
                else None,
            }

    except Exception as e:
        logger.warning(f"DSPy refinement failed: {e}")
        return {"refined_query": user_query, "year": None, "subject": None, "branch": None}


def _safe_int(val: JSONValue) -> int | None:
    """يحاول تحويل القيمة إلى عدد صحيح مع تجاهل القيم غير الصالحة."""
    try:
        if val and str(val).lower() != "none":
            return int(str(val))
    except (TypeError, ValueError):
        return None
    return None
