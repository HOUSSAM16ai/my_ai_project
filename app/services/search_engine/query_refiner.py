import dspy
import json
from typing import Optional, Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)

class StructuredQuerySignature(dspy.Signature):
    """
    Analyze the educational query to extract specific metadata and a refined search term.
    Focus on extracting:
    - year: The exam year (e.g., 2024, 2023).
    - subject: The academic subject (e.g., Mathematics, Physics).
    - branch: The study branch (e.g., Experimental Sciences, Math Tech).
    - refined_query: A clean, English translation of the core topic for vector search (e.g., "Probability exercises", "Complex numbers").
    """
    user_query: str = dspy.InputField(desc="The raw query from the student.")
    refined_query: str = dspy.OutputField(desc="The optimized search term.")
    year: Optional[int] = dspy.OutputField(desc="The exam year if mentioned, else None.")
    subject: Optional[str] = dspy.OutputField(desc="The subject name if mentioned, else None.")
    branch: Optional[str] = dspy.OutputField(desc="The branch name if mentioned, else None.")

class StructuredQueryRefiner(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(StructuredQuerySignature)

    def forward(self, user_query: str):
        return self.prog(user_query=user_query)

def get_refined_query(user_query: str, api_key: str, model_name: str = "mistralai/devstral-2512:free") -> Dict[str, Any]:
    """
    Uses DSPy to refine the query and extract metadata.
    Returns a dictionary with 'refined_query', 'year', 'subject', 'branch'.
    """
    try:
        lm = dspy.LM(
            model=f"openai/{model_name}",
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            max_tokens=300
        )

        with dspy.context(lm=lm):
            refiner = StructuredQueryRefiner()
            result = refiner(user_query=user_query)

            # Extract and clean
            return {
                "refined_query": result.refined_query,
                "year": _safe_int(result.year),
                "subject": result.subject if result.subject and result.subject.lower() != "none" else None,
                "branch": result.branch if result.branch and result.branch.lower() != "none" else None
            }

    except Exception as e:
        logger.warning(f"DSPy refinement failed: {e}")
        return {"refined_query": user_query}

def _safe_int(val: Any) -> Optional[int]:
    try:
        if val and str(val).lower() != "none":
            return int(str(val))
    except:
        pass
    return None
