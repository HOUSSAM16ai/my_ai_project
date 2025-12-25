"""
واجهة التصدير العامة لخدمة عميل LLM.
Public export interface for LLM Client service.
"""

from app.services.llm_client.service import (
    invoke_chat,
    invoke_chat_stream,
    register_llm_post_hook,
    register_llm_pre_hook,
    get_llm_client
)
from app.services.llm_client.domain.models import LLMPayload, LLMResponseEnvelope

__all__ = [
    "invoke_chat",
    "invoke_chat_stream",
    "register_llm_post_hook",
    "register_llm_pre_hook",
    "get_llm_client",
    "LLMPayload",
    "LLMResponseEnvelope"
]
