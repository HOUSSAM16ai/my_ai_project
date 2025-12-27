"""
واجهة التصدير العامة لخدمة عميل LLM.
Public export interface for LLM Client service.
"""

from app.services.llm_client.domain.models import LLMPayload, LLMResponseEnvelope
from app.services.llm_client.service import (
    get_llm_client,
    invoke_chat,
    invoke_chat_stream,
    register_llm_post_hook,
    register_llm_pre_hook,
)

__all__ = [
    "LLMPayload",
    "LLMResponseEnvelope",
    "get_llm_client",
    "invoke_chat",
    "invoke_chat_stream",
    "register_llm_post_hook",
    "register_llm_pre_hook"
]
