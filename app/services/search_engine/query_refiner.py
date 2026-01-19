import dspy

from app.core.logging import get_logger

logger = get_logger(__name__)

# Configure DSPy with the user's preferred model
# The user specified: mistralai/devstral-2512:free via OpenRouter
# And provided an API Key.

class QueryRefinementSignature(dspy.Signature):
    """
    Refine a natural language educational query into a precise semantic search query.
    Normalize terms like 'Exercise One' to 'Exercise 1', 'First Subject' to 'Subject 1'.
    Extract key metadata if possible.
    """
    user_query = dspy.InputField(desc="The raw query from the student.")
    refined_query = dspy.OutputField(desc="The optimized query for vector search, emphasizing exam year, subject, and exercise number.")

class QueryRefiner(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(QueryRefinementSignature)

    def forward(self, user_query: str):
        return self.prog(user_query=user_query)

def get_refined_query(user_query: str, api_key: str, model_name: str = "mistralai/devstral-2512:free") -> str:
    """
    Uses DSPy to refine the query.
    """
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
        logger.warning("DSPy refinement failed: %s", e)
        return user_query
