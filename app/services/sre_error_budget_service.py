
from app.services.sre_error_budget.facade import SreErrorBudgetFacade

# Alias for compatibility if needed, or re-export
SREErrorBudgetService = SreErrorBudgetFacade

_sre_service_instance = None

def get_sre_service() -> SREErrorBudgetService:
    global _sre_service_instance
    if _sre_service_instance is None:
        _sre_service_instance = SreErrorBudgetFacade()
    return _sre_service_instance
