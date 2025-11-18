# app/services/ai_service_gateway.py
"""
This module provides a backward-compatibility layer for the AIServiceGateway.
New applications SHOULD NOT use this module directly. Instead, they should
import the AIServiceGateway from app.gateways.ai_service_gateway and instantiate
it via the DI factory.

Legacy imports will continue working until this module is removed in a future
milestone.
"""

import warnings

from app.gateways.ai_service_gateway import get_ai_service_gateway as get_new_gateway


def get_ai_service_gateway():
    """
    Deprecated: This function is for backward compatibility only.
    Use the factory in app.gateways.ai_service_gateway instead.
    """
    warnings.warn(
        "get_ai_service_gateway from app.services is deprecated.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_new_gateway()


# You can add wrappers for other functions if they existed in the original file
# For example:
#
# def stream_chat(question: str, conversation_id: str | None, user_id: int | str):
#     warnings.warn(
#         "stream_chat from app.services is deprecated.",
#         DeprecationWarning,
#         stacklevel=2,
#     )
#     return get_new_gateway().stream_chat(question, conversation_id, user_id)
