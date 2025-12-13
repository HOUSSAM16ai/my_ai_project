"""
SreErrorBudget Facade
"""

from .application import SreErrorBudgetManager
from .infrastructure import InMemorySreErrorBudgetRepository


class SreErrorBudgetFacade:
    """
    Facade for SreErrorBudget
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemorySreErrorBudgetRepository()
        self._manager = SreErrorBudgetManager(self._repository)

    # Add your public methods here
