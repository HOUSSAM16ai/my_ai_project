import uuid

from app.core.gateway.simple_client import SimpleAIClient
from app.core.interfaces import IReasoningStrategy
from app.core.logging import get_logger
from microservices.reasoning_agent.src.models import EvaluationResult, ReasoningNode

logger = get_logger("reasoning-strategy")


class RMCTSStrategy(IReasoningStrategy):
    """
    Implements a simplified Recursive Monte Carlo Tree Search (R-MCTS)
    adapted for Inference-Time Reasoning.

    Phases:
    1. Expansion: Generate candidate thoughts.
    2. Simulation (Reflection): Evaluate candidates.
    3. Backpropagation: Update values (implied by selection).
    4. Selection: Pick best path.
    """

    def __init__(self, ai_client: SimpleAIClient):
        self.ai_client = ai_client

    async def expand(self, parent: ReasoningNode, context: str) -> list[ReasoningNode]:
        """
        Generates N possible next steps/thoughts based on the parent.
        """
        prompt = (
            f"Context: {context}\n"
            f"Previous Thought: {parent.content}\n\n"
            "Task: Generate 3 distinct, high-quality reasoning steps or hypotheses to progress towards the answer.\n"
            "Format: 1. [Thought 1]\n2. [Thought 2]\n3. [Thought 3]"
        )

        response = await self.ai_client.generate_text(
            prompt=prompt, system_prompt="You are a Strategic Reasoning Engine. Think diversely."
        )

        # Simple parsing logic
        lines = response.content.split("\n")
        candidates = []
        for line in lines:
            if line.strip() and (line[0].isdigit() or line.startswith("-")):
                clean_content = line.lstrip("1234567890.- ").strip()
                if clean_content:
                    candidates.append(
                        ReasoningNode(
                            id=str(uuid.uuid4()),
                            parent_id=parent.id,
                            content=clean_content,
                            step_type="hypothesis",
                        )
                    )

        return candidates[:3]  # Limit to top 3

    async def evaluate(self, node: ReasoningNode, context: str) -> EvaluationResult:
        """
        Reflective step: Score the thought against the context.
        """
        prompt = (
            f"Context: {context}\n"
            f"Proposed Thought: {node.content}\n\n"
            "Task: Evaluate this thought for accuracy, relevance, and logical soundness.\n"
            "Output format:\n"
            "Score: [0.0-1.0]\n"
            "Valid: [True/False]\n"
            "Reason: [Explanation]"
        )

        response = await self.ai_client.generate_text(
            prompt=prompt, system_prompt="You are a Critical Reviewer. Be strict."
        )

        text = response.content.lower()

        # Naive parsing (Robust implementation would use Structured Output / JSON)
        score = 0.5
        is_valid = True

        try:
            for line in text.split("\n"):
                if "score:" in line:
                    score = float(line.split(":")[1].strip())
                if "valid:" in line:
                    is_valid = "true" in line
        except Exception:
            pass

        return EvaluationResult(score=score, is_valid=is_valid, reasoning=text)

    async def execute(self, root_content: str, context: str, depth: int = 2) -> ReasoningNode:
        """
        Executes the search strategy.
        """
        root = ReasoningNode(
            id=str(uuid.uuid4()), content=root_content, step_type="root", value=1.0
        )

        current_layer = [root]

        for i in range(depth):
            logger.info(f"R-MCTS Depth {i + 1}: Expanding {len(current_layer)} nodes")
            next_layer = []

            # Expansion Phase
            for node in current_layer:
                children = await self.expand(node, context)
                node.children = children

                # Evaluation Phase
                for child in children:
                    eval_result = await self.evaluate(child, context)
                    child.evaluation = eval_result
                    child.value = eval_result.score
                    # Basic Pruning
                    if child.evaluation.is_valid and child.evaluation.score > 0.6:
                        next_layer.append(child)

            # Selection Phase (Greedy for now, keeping top 2)
            next_layer.sort(key=lambda x: x.value, reverse=True)
            current_layer = next_layer[:2]

            if not current_layer:
                logger.warning("All paths pruned. Backtracking not implemented in v1.")
                break

        # Return the best leaf node
        if not current_layer:
            return root  # Fallback
        return current_layer[0]


class MathReasoningStrategy(RMCTSStrategy):
    """
    Overmind Education Strategy (Specialized for Math/Probability).
    Enforces a structured 4-Step Pedagogical Process:
    1. Modeling: Define Sample Space, Events, Variables.
    2. Strategy Selection: Choose the Theorem (Bayes, Total Prob, etc.).
    3. Calculation: Perform steps with checks.
    4. Pedagogical Reflection: Explain 'Why'.
    """

    async def expand(self, parent: ReasoningNode, context: str) -> list[ReasoningNode]:
        """
        Specialized expansion for Math problems.
        """
        # We determine the 'phase' based on the parent's content or depth implicitly
        # But here we ask the LLM to generate the NEXT logical mathematical step.
        prompt = (
            f"Context: {context}\n"
            f"Current Progress: {parent.content}\n\n"
            "Task: You are a Math Professor. Propose 3 distinct ways to proceed with this probability problem.\n"
            "Options should cover:\n"
            "1. Formal Modeling (Defining Events/Variables)\n"
            "2. Visual Approach (Tree Diagram/Table)\n"
            "3. Formula Application (Direct calculation)\n"
            "Format: 1. [Method 1]\n2. [Method 2]\n3. [Method 3]"
        )

        response = await self.ai_client.generate_text(
            prompt=prompt, system_prompt="You are an expert Math Tutor. Be precise and pedagogical."
        )

        # Reuse parsing logic
        lines = response.content.split("\n")
        candidates = []
        for line in lines:
            if line.strip() and (line[0].isdigit() or line.startswith("-")):
                clean_content = line.lstrip("1234567890.- ").strip()
                if clean_content:
                    candidates.append(
                        ReasoningNode(
                            id=str(uuid.uuid4()),
                            parent_id=parent.id,
                            content=clean_content,
                            step_type="math_step",
                        )
                    )

        return candidates[:3]

    async def evaluate(self, node: ReasoningNode, context: str) -> EvaluationResult:
        """
        Math-specific evaluation: Checks for Correctness and Educational Value.
        """
        prompt = (
            f"Context: {context}\n"
            f"Proposed Step: {node.content}\n\n"
            "Task: Evaluate this mathematical step.\n"
            "Criteria:\n"
            "1. Mathematical Correctness (Is the formula/logic right?)\n"
            "2. Pedagogical Clarity (Is it easy to understand for a student?)\n"
            "Output format:\n"
            "Score: [0.0-1.0]\n"
            "Valid: [True/False]\n"
            "Reason: [Critique]"
        )

        response = await self.ai_client.generate_text(
            prompt=prompt, system_prompt="You are a Strict Exam Grader."
        )

        text = response.content.lower()
        score = 0.5
        is_valid = True

        try:
            for line in text.split("\n"):
                if "score:" in line:
                    score = float(line.split(":")[1].strip())
                if "valid:" in line:
                    is_valid = "true" in line
        except Exception:
            pass

        return EvaluationResult(score=score, is_valid=is_valid, reasoning=text)
