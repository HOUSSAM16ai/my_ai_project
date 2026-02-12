from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PlanningGatewayProtocol(Protocol):
    """
    Protocol for Planning Agent capabilities.
    Acts as an ACL to the Planning Domain.
    """

    async def generate_plan(
        self,
        goal: str,
        context: str = "",
    ) -> Any:
        """
        Generate a cognitive plan for a goal.
        Returns a PlanResult object (or similar structure).
        """
        ...
