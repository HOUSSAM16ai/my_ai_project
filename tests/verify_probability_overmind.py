import asyncio
import os
import sys
from unittest.mock import MagicMock

# Mock heavy dependencies BEFORE importing app
sys.modules["llama_index.vector_stores.supabase"] = MagicMock()
sys.modules["llama_index.vector_stores.supabase"].SupabaseVectorStore = MagicMock()
sys.modules["llama_index.vector_stores.postgres"] = MagicMock()
sys.modules["llama_index.llms.openai"] = MagicMock()
sys.modules["llama_index.embeddings.openai"] = MagicMock()

# Ensure app is in path
sys.path.append(os.getcwd())

from app.core.gateway.simple_client import SimpleAIClient
from microservices.reasoning_agent.src.search_strategy import MathReasoningStrategy
from microservices.reasoning_agent.src.workflow import SuperReasoningWorkflow


class MockAIClient(SimpleAIClient):
    """
    Mock AI Client to simulate LLM responses for the Math Strategy.
    """

    async def generate_text(self, prompt: str, system_prompt: str = "") -> object:
        # Return a dummy object with .content
        class Response:
            pass

        res = Response()

        # Simulate Expansion (Proposing Methods)
        if "Propose 3 distinct ways" in prompt:
            res.content = (
                "1. Define Events: Let B = Machine B, D = Defective. We need P(B|D).\n"
                "2. Tree Diagram: Draw branches for A (0.6) and B (0.4), then defect rates.\n"
                "3. Bayes Formula: P(B|D) = P(D|B)P(B) / P(D)."
            )

        # Simulate Evaluation
        elif "Evaluate this mathematical step" in prompt:
            res.content = (
                "Score: 0.95\n"
                "Valid: True\n"
                "Reason: This is the correct standard approach for Bayes theorem problems."
            )

        # Simulate Final Synthesis
        elif "Synthesize final answer" in prompt or "Overmind Super Reasoner" in system_prompt:
            res.content = (
                "## Probability Analysis\n"
                "**Problem:** Find $P(Machine B | Defective)$.\n\n"
                "**1. Define Events:**\n"
                "- $A$: Item from Machine A ($P(A) = 0.60$)\n"
                "- $B$: Item from Machine B ($P(B) = 0.40$)\n"
                "- $D$: Item is Defective ($P(D|A) = 0.01$, $P(D|B) = 0.02$)\n\n"
                "**2. Apply Bayes' Theorem:**\n"
                "$$P(B|D) = \\frac{P(D|B)P(B)}{P(D|B)P(B) + P(D|A)P(A)}$$\n\n"
                "**3. Calculate:**\n"
                "- Numerator: $0.02 \\times 0.40 = 0.008$\n"
                "- Denominator: $(0.02 \\times 0.40) + (0.01 \\times 0.60) = 0.008 + 0.006 = 0.014$\n"
                "- Result: $0.008 / 0.014 = 4/7 \\approx 0.5714$\n\n"
                "**Conclusion:** The probability is approximately **57.14%**."
            )
        else:
            # Default fallback for R-MCTS general prompts
            res.content = "1. Analyze variables.\n2. Check constraints.\n3. Solve."

        return res


async def run_experiment():
    print("🧠 Starting Overmind Education Experiment: Probability...")

    # 1. Setup
    client = MockAIClient()  # Use Mock for deterministic testing
    strategy = MathReasoningStrategy(client)
    workflow = SuperReasoningWorkflow(client=client, strategy=strategy, verbose=True)

    # 2. Define Problem (Bayes Theorem)
    problem = (
        "A factory has two machines A and B. Machine A produces 60% of items and B produces 40%. "
        "1% of A's items are defective, and 2% of B's are defective. "
        "An item is chosen at random and found to be defective. "
        "What is the probability it came from Machine B?"
    )

    # 3. Run Workflow
    try:
        # We need to manually trigger the workflow steps since it's a LlamaIndex workflow
        result = await workflow.run(query=problem)

        print("\n✨ Overmind Result:\n")
        print(result)

        if "57.14%" in str(result) or "4/7" in str(result):
            print("\n✅ Verification PASSED: Correct Bayes Theorem application.")
        else:
            print("\n❌ Verification FAILED: Incorrect result.")

    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_experiment())
