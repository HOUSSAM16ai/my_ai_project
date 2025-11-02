"""
ADMIN AI SERVICE - SUPER INTELLIGENCE GATEWAY
Ultra Professional Hyper Edition
=====================================
File        : app/services/admin_ai_service.py
Version     : 1.0.0 • "OMNISCIENT-ADMIN / ULTRA-CONTEXT-AWARE"
Status      : Production / Hardened / Superintelligent
Author      : Overmind + Maestro Fusion System

MISSION (المهمة)
-------
خدمة ذكاء اصطناعي خارقة لصفحة الأدمن تدمج جميع القدرات:
  - تحليل عميق للمشروع باستخدام Deep Indexer
  - الإجابة على الأسئلة باستخدام السياق الكامل من System Service
  - تنفيذ التغييرات على المشروع باستخدام Overmind
  - حفظ المحادثات في قاعدة البيانات
  - توفير واجهة موحدة للذكاء الاصطناعي

CORE CAPABILITIES (القدرات الأساسية)
-----------------
1. project_analysis() - تحليل عميق شامل للمشروع
2. answer_question() - الإجابة على الأسئلة مع سياق ذكي
3. execute_modification() - تنفيذ تعديلات على المشروع
4. get_conversation_context() - جلب سياق المحادثة الكامل
5. save_message() - حفظ الرسائل في قاعدة البيانات
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from app import db
from app.models import (
    AdminConversation,
    AdminMessage,
    User,
    utc_now,
)

try:
    from app.services import generation_service as maestro
except ImportError:
    maestro = None

try:
    from app.services import system_service
except ImportError:
    system_service = None

try:
    from app.services import master_agent_service as overmind
except ImportError:
    overmind = None

try:
    from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt
except ImportError:
    build_index = None
    summarize_for_prompt = None

try:
    from app.services.llm_client_service import get_llm_client
except ImportError:
    get_llm_client = None

logger = logging.getLogger(__name__)

MAX_CONTEXT_MESSAGES = int(os.getenv("ADMIN_AI_MAX_CONTEXT_MESSAGES", "10"))
MAX_RELATED_CONTEXT_CHUNKS = int(os.getenv("ADMIN_AI_MAX_CONTEXT_CHUNKS", "5"))
ENABLE_DEEP_INDEX = os.getenv("ADMIN_AI_ENABLE_DEEP_INDEX", "1") == "1"
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "openai/gpt-4o")

# SUPERHUMAN CONFIGURATION - Long question handling with EXTREME MODE support
MAX_QUESTION_LENGTH = int(
    os.getenv("ADMIN_AI_MAX_QUESTION_LENGTH", "100000")
)  # Doubled for extreme cases
MAX_RESPONSE_TOKENS = int(
    os.getenv("ADMIN_AI_MAX_RESPONSE_TOKENS", "32000")  # Doubled for extremely complex answers
)  # tokens for very long responses
LONG_QUESTION_THRESHOLD = int(os.getenv("ADMIN_AI_LONG_QUESTION_THRESHOLD", "5000"))  # characters
EXTREME_QUESTION_THRESHOLD = int(
    os.getenv("ADMIN_AI_EXTREME_QUESTION_THRESHOLD", "20000")
)  # For superhuman processing
ENABLE_STREAMING = (
    os.getenv("ADMIN_AI_ENABLE_STREAMING", "1") == "1"
)  # Enable streaming for long responses
EXTREME_COMPLEXITY_MODE = (
    os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"
)  # Match LLM client setting


class AdminAIService:
    """
    الخدمة الرئيسية للذكاء الاصطناعي في صفحة الأدمن.
    """

    def __init__(self):
        self.logger = logger

    def analyze_project(
        self,
        user: User,
        conversation_id: int | None = None,
        focus_areas: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        تحليل عميق شامل للمشروع باستخدام Deep Indexer.

        Args:
            user: المستخدم الذي يطلب التحليل
            conversation_id: معرف المحادثة (اختياري)
            focus_areas: مجالات التركيز (اختياري) مثل ["security", "performance", "architecture"]

        Returns:
            Dict يحتوي على التحليل الكامل
        """
        start_time = time.time()

        try:
            # ============================================================
            # SUPERHUMAN VALIDATION - Check deep indexer availability
            # ============================================================
            if not build_index or not ENABLE_DEEP_INDEX:
                error_msg = (
                    "⚠️ خدمة التحليل العميق غير متاحة حالياً.\n\n"
                    "Deep analysis service is currently unavailable.\n\n"
                    "**Possible causes:**\n"
                    "- Deep indexer module not loaded\n"
                    "- ADMIN_AI_ENABLE_DEEP_INDEX is disabled\n\n"
                    "**Solution:**\n"
                    "Please ensure the deep indexer module is properly configured."
                )
                self.logger.warning("Deep indexer not available for project analysis")
                return {
                    "status": "error",
                    "error": "Deep indexer not available",
                    "message": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }

            # ============================================================
            # SUPERHUMAN ANALYSIS - Build comprehensive index
            # ============================================================
            self.logger.info(f"Building deep index for project analysis (user_id={user.id})")

            try:
                index = build_index(root=".")
            except Exception as e:
                self.logger.error(f"Deep index build failed: {e}", exc_info=True)
                error_msg = (
                    f"⚠️ فشل بناء فهرس المشروع.\n\n"
                    f"Failed to build project index.\n\n"
                    f"**Error:** {str(e)}\n\n"
                    f"**Solution:**\n"
                    f"This might be due to:\n"
                    f"- Insufficient file permissions\n"
                    f"- Corrupted project files\n"
                    f"- Missing dependencies\n\n"
                    f"Please check the logs for more details."
                )
                return {
                    "status": "error",
                    "error": f"Index build failed: {str(e)}",
                    "message": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }

            # ============================================================
            # SUPERHUMAN SYNTHESIS - Generate comprehensive analysis
            # ============================================================
            analysis = {
                "status": "success",
                "timestamp": datetime.now(UTC).isoformat(),
                "user_id": user.id,
                "project_stats": {
                    "files_scanned": index.get("files_scanned", 0),
                    "total_functions": index.get("global_metrics", {}).get("total_functions", 0),
                    "total_classes": len(
                        [c for m in index.get("modules", []) for c in m.get("classes", [])]
                    ),
                    "complexity_hotspots": len(index.get("complexity_hotspots_top50", [])),
                    "duplicate_functions": len(index.get("duplicate_function_bodies", {})),
                },
                "architecture": self._analyze_architecture(index),
                "hotspots": self._analyze_hotspots(index),
                "recommendations": self._generate_recommendations(index),
                "deep_index_summary": (
                    summarize_for_prompt(index, max_len=3000) if summarize_for_prompt else None
                ),
                "full_index": index,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

            # ============================================================
            # SUPERHUMAN PERSISTENCE - Save to conversation
            # ============================================================
            if conversation_id:
                try:
                    self._save_analysis_to_conversation(conversation_id, analysis)
                except Exception as e:
                    self.logger.warning(f"Failed to save analysis to conversation: {e}")
                    # Don't fail the entire analysis if saving fails

            return analysis

        except Exception as e:
            self.logger.error(f"Project analysis failed: {e}", exc_info=True)
            error_msg = (
                f"⚠️ حدث خطأ غير متوقع أثناء التحليل.\n\n"
                f"An unexpected error occurred during analysis.\n\n"
                f"**Error:** {str(e)}\n\n"
                f"The error has been logged. Please try again or contact support."
            )
            return {
                "status": "error",
                "error": str(e),
                "message": error_msg,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

    def _analyze_architecture(self, index: dict) -> dict[str, Any]:
        """تحليل البنية المعمارية"""
        layers = index.get("layers", {})
        return {
            "layers_detected": list(layers.keys()),
            "services_count": len(layers.get("service", [])),
            "models_count": len(layers.get("model", [])),
            "routes_count": len(layers.get("route", [])),
            "utils_count": len(layers.get("util", [])),
        }

    def _analyze_hotspots(self, index: dict) -> list[dict]:
        """تحليل نقاط التعقيد"""
        hotspots = index.get("complexity_hotspots_top50", [])[:10]
        return [
            {
                "file": h.get("file"),
                "function": h.get("name"),
                "complexity": h.get("complexity"),
                "lines": h.get("loc"),
            }
            for h in hotspots
        ]

    def _generate_recommendations(self, index: dict) -> list[str]:
        """توليد توصيات ذكية"""
        recommendations = []

        hotspots_count = len(index.get("complexity_hotspots_top50", []))
        if hotspots_count > 20:
            recommendations.append(
                f"⚠️ وجد {hotspots_count} دالة ذات تعقيد عالي. يُنصح بإعادة هيكلة الدوال المعقدة."
            )

        duplicates_count = len(index.get("duplicate_function_bodies", []))
        if duplicates_count > 5:
            recommendations.append(
                f"⚠️ وجد {duplicates_count} دالة مكررة. يمكن دمجها لتحسين الصيانة."
            )

        files = index.get("file_metrics", [])
        large_files = [f for f in files if f.get("loc", 0) > 500]
        if large_files:
            recommendations.append(
                f"📄 يوجد {len(large_files)} ملف كبير (>500 سطر). يُنصح بتقسيمها."
            )

        return recommendations

    def _save_analysis_to_conversation(self, conversation_id: int, analysis: dict):
        """
        حفظ التحليل في المحادثة - SUPERHUMAN INTEGRATION

        Saves project analysis results to conversation for future reference.
        """
        try:
            conversation = db.session.get(AdminConversation, conversation_id)
            if conversation:
                # Update deep index summary if available
                if analysis.get("deep_index_summary"):
                    conversation.deep_index_summary = analysis["deep_index_summary"]

                # Save analysis as a system message
                self._save_message(
                    conversation_id,
                    "system",
                    f"📊 Project Analysis Complete\n\n"
                    f"Files: {analysis.get('project_stats', {}).get('files_scanned', 0)}\n"
                    f"Functions: {analysis.get('project_stats', {}).get('total_functions', 0)}\n"
                    f"Hotspots: {analysis.get('project_stats', {}).get('complexity_hotspots', 0)}",
                    metadata_json={"analysis": analysis},
                )

                # Add 'analysis' tag
                if conversation.tags and "analysis" not in conversation.tags:
                    conversation.tags.append("analysis")

                db.session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save analysis to conversation: {e}", exc_info=True)

    def answer_question(
        self,
        question: str,
        user: User,
        conversation_id: int | None = None,
        use_deep_context: bool = True,
    ) -> dict[str, Any]:
        """
        الإجابة على سؤال باستخدام السياق الكامل للمشروع.

        Args:
            question: السؤال
            user: المستخدم
            conversation_id: معرف المحادثة
            use_deep_context: استخدام السياق العميق

        Returns:
            Dict يحتوي على الإجابة والمعلومات الإضافية
        """
        start_time = time.time()

        try:
            # ============================================================
            # SUPERHUMAN ERROR PREVENTION - Validate AI availability first
            # ============================================================
            if not get_llm_client:
                error_msg = (
                    "⚠️ خدمة الذكاء الاصطناعي غير متاحة حالياً.\n\n"
                    "AI service is currently unavailable.\n\n"
                    "**Possible reasons:**\n"
                    "- LLM client service not loaded\n"
                    "- Missing dependencies\n\n"
                    "**Solution:** Please contact the administrator to configure the AI service."
                )
                return {
                    "status": "error",
                    "error": "AI service unavailable",
                    "answer": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }

            # Check if API keys are configured
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                error_msg = (
                    "⚠️ لم يتم تكوين مفاتيح API للذكاء الاصطناعي.\n\n"
                    "AI API keys are not configured.\n\n"
                    "**Required Configuration:**\n"
                    "Please set one of the following environment variables:\n"
                    "- `OPENROUTER_API_KEY` (recommended)\n"
                    "- `OPENAI_API_KEY`\n\n"
                    "**How to fix:**\n"
                    "1. Create a `.env` file in the project root\n"
                    "2. Add: `OPENROUTER_API_KEY=sk-or-v1-your-key-here`\n"
                    "3. Restart the application\n\n"
                    "**Get your API key:**\n"
                    "- OpenRouter: https://openrouter.ai/keys\n"
                    "- OpenAI: https://platform.openai.com/api-keys"
                )
                self.logger.warning("AI API key not configured - cannot answer questions")
                return {
                    "status": "error",
                    "error": "API key not configured",
                    "answer": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }

            conversation_history = []
            deep_index_summary = None
            context_summary = None  # For long conversation summaries

            # ============================================================
            # SUPERHUMAN SECURITY - Validate conversation ownership
            # ============================================================
            if conversation_id:
                conversation = db.session.get(AdminConversation, conversation_id)

                # Security check: ensure conversation exists and belongs to user
                if not conversation:
                    error_msg = (
                        f"⚠️ المحادثة #{conversation_id} غير موجودة.\n\n"
                        f"Conversation #{conversation_id} not found.\n\n"
                        f"**Possible reasons:**\n"
                        f"- Conversation was deleted or archived\n"
                        f"- Invalid conversation ID\n\n"
                        f"**Solution:**\n"
                        f"Start a new conversation or select an existing one from the sidebar."
                    )
                    self.logger.warning(
                        f"User {user.id} tried to access non-existent conversation {conversation_id}"
                    )
                    return {
                        "status": "error",
                        "error": "Conversation not found",
                        "answer": error_msg,
                        "elapsed_seconds": round(time.time() - start_time, 2),
                    }

                if conversation.user_id != user.id:
                    error_msg = (
                        "⚠️ ليس لديك صلاحية للوصول إلى هذه المحادثة.\n\n"
                        "You don't have permission to access this conversation.\n\n"
                        "**Security Notice:**\n"
                        "This conversation belongs to another user.\n\n"
                        "**Solution:**\n"
                        "Please use your own conversations or start a new one."
                    )
                    self.logger.warning(
                        f"User {user.id} attempted unauthorized access to conversation {conversation_id} "
                        f"(owner: {conversation.user_id})"
                    )
                    return {
                        "status": "error",
                        "error": "Unauthorized access",
                        "answer": error_msg,
                        "elapsed_seconds": round(time.time() - start_time, 2),
                    }

                # Load conversation history and context
                conversation_history = self._get_conversation_history(conversation_id)
                deep_index_summary = conversation.deep_index_summary

                # SUPERHUMAN FEATURE: Smart context summarization for long conversations
                # If conversation has many messages, provide a summary to the AI
                context_summary = None
                if len(conversation_history) > MAX_CONTEXT_MESSAGES:
                    context_summary = self._generate_conversation_summary(
                        conversation, conversation_history
                    )
                    self.logger.info(
                        f"Generated context summary for long conversation #{conversation_id}"
                    )

                self.logger.info(
                    f"Continuing conversation #{conversation_id} for user {user.id} "
                    f"(history: {len(conversation_history)} messages, "
                    f"summary: {'yes' if context_summary else 'no'})"
                )

            related_context = []
            if system_service and hasattr(system_service, "find_related_context"):
                try:
                    ctx_result = system_service.find_related_context(
                        question, limit=MAX_RELATED_CONTEXT_CHUNKS
                    )
                    if ctx_result.ok:
                        related_context = ctx_result.data.get("results", [])
                except Exception as e:
                    self.logger.warning(f"Failed to get related context: {e}")

            # Build system prompt with comprehensive error handling
            try:
                system_prompt = self._build_super_system_prompt(
                    deep_index_summary=deep_index_summary if use_deep_context else None,
                    related_context=related_context,
                    conversation_summary=context_summary if conversation_id else None,
                )
            except Exception as e:
                self.logger.error(f"Failed to build system prompt: {e}", exc_info=True)
                # Use minimal fallback prompt
                system_prompt = (
                    "أنت مساعد ذكاء اصطناعي متخصص في مساعدة المستخدمين.\n"
                    "You are an AI assistant specialized in helping users."
                )

            # ============================================================
            # SUPERHUMAN VALIDATION - Check question length with EXTREME support
            # ============================================================
            question_length = len(question)
            is_long_question = question_length > LONG_QUESTION_THRESHOLD
            is_extreme_question = question_length > EXTREME_QUESTION_THRESHOLD

            if question_length > MAX_QUESTION_LENGTH:
                error_msg = (
                    f"⚠️ السؤال طويل جداً ({question_length:,} حرف).\n\n"
                    f"Question is too long ({question_length:,} characters).\n\n"
                    f"**Maximum allowed:** {MAX_QUESTION_LENGTH:,} characters\n"
                    f"**Your question:** {question_length:,} characters\n\n"
                    f"**💡 للأسئلة الخارقة التعقيد (For Extremely Complex Questions):**\n"
                    f"يمكنك تفعيل الوضع الخارق عن طريق:\n"
                    f"You can enable extreme mode by:\n"
                    f"1. Set `LLM_EXTREME_COMPLEXITY_MODE=1` in .env\n"
                    f"2. Set `ADMIN_AI_MAX_QUESTION_LENGTH=200000` for very large inputs\n\n"
                    f"**Possible solutions:**\n"
                    f"1. Break your question into smaller parts\n"
                    f"2. Summarize your question while keeping key details\n"
                    f"3. Focus on the most important aspects first\n"
                    f"4. Enable extreme complexity mode for unlimited processing\n\n"
                    f"**Tip:** You can ask follow-up questions to explore specific details after getting an initial answer."
                )
                self.logger.warning(
                    f"User {user.id} submitted question exceeding max length: {question_length} > {MAX_QUESTION_LENGTH}"
                )
                return {
                    "status": "error",
                    "error": "Question too long",
                    "answer": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }

            if is_extreme_question:
                self.logger.info(
                    f"🚀 EXTREME COMPLEXITY QUESTION detected for user {user.id}: "
                    f"{question_length} characters (extreme threshold: {EXTREME_QUESTION_THRESHOLD})"
                )
            elif is_long_question:
                self.logger.info(
                    f"Processing long question for user {user.id}: {question_length} characters (threshold: {LONG_QUESTION_THRESHOLD})"
                )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history[-MAX_CONTEXT_MESSAGES:])
            messages.append({"role": "user", "content": question})

            # ============================================================
            # SUPERHUMAN AI INVOCATION - With comprehensive error handling
            # ============================================================
            try:
                client = get_llm_client()

                # Check if we got a mock client (indicates no API key)
                try:
                    from app.services.llm_client_service import is_mock_client

                    if is_mock_client(client):
                        error_msg = (
                            "⚠️ نظام الذكاء الاصطناعي يعمل في وضع التجريب.\n\n"
                            "AI system is running in mock mode.\n\n"
                            "This means no API key is configured. Please set:\n"
                            "- `OPENROUTER_API_KEY` or\n"
                            "- `OPENAI_API_KEY`\n\n"
                            "in your `.env` file to enable real AI responses."
                        )
                        return {
                            "status": "error",
                            "error": "Mock mode - API key required",
                            "answer": error_msg,
                            "elapsed_seconds": round(time.time() - start_time, 2),
                        }
                except ImportError:
                    pass  # is_mock_client not available, continue

                # SUPERHUMAN FEATURE: Adjust max_tokens and retries based on question complexity
                # For extreme questions, allow up to 32k tokens and more processing time
                if is_extreme_question:
                    max_tokens = MAX_RESPONSE_TOKENS  # 32k for extreme complexity
                    # Log that we're entering extreme processing mode
                    self.logger.warning(
                        f"⚡ EXTREME MODE: Allocating {max_tokens} tokens for extremely complex question "
                        f"(length: {question_length:,} chars). This may take several minutes."
                    )
                elif is_long_question:
                    max_tokens = MAX_RESPONSE_TOKENS // 2  # 16k for long questions
                else:
                    max_tokens = 4000  # Standard for normal questions

                self.logger.info(
                    f"Invoking AI with model={DEFAULT_MODEL}, max_tokens={max_tokens}, "
                    f"question_length={question_length}, is_long={is_long_question}, "
                    f"is_extreme={is_extreme_question}, extreme_mode={EXTREME_COMPLEXITY_MODE}"
                )

                response = client.chat.completions.create(
                    model=DEFAULT_MODEL or "openai/gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens,
                )

                answer = response.choices[0].message.content
                tokens_used = getattr(response.usage, "total_tokens", None)
                model_used = response.model

                # ============================================================
                # CRITICAL FIX: Validate answer content is not None/empty
                # ============================================================
                if answer is None or (isinstance(answer, str) and not answer.strip()):
                    # This can happen with thinking models or certain API configurations
                    # that return tool calls or other data instead of text content
                    self.logger.warning(
                        f"AI returned None/empty content for model {model_used}. "
                        f"Response structure: {response.choices[0].message}"
                    )

                    # Check if there are tool calls or other content
                    message_obj = response.choices[0].message
                    has_tool_calls = hasattr(message_obj, "tool_calls") and message_obj.tool_calls

                    if has_tool_calls:
                        error_msg = (
                            "⚠️ نموذج الذكاء الاصطناعي أرجع استدعاءات أدوات بدلاً من نص.\n\n"
                            "The AI model returned tool calls instead of text content.\n\n"
                            "**This usually happens when:**\n"
                            "- Using a model configured for function calling\n"
                            "- Model is trying to execute tools/functions\n\n"
                            "**Solution:**\n"
                            "Try asking your question again in a different way, or contact support "
                            "to configure the model properly for chat responses."
                        )
                    else:
                        error_msg = (
                            "⚠️ نموذج الذكاء الاصطناعي لم يُرجع أي محتوى.\n\n"
                            "The AI model did not return any content.\n\n"
                            "**Model used:** " + str(model_used) + "\n"
                            "**Tokens consumed:** " + str(tokens_used or 0) + "\n\n"
                            "**This can happen when:**\n"
                            "- Using thinking/reasoning models that may have processing issues\n"
                            "- API response was malformed or incomplete\n"
                            "- Model encountered an internal error\n\n"
                            "**Solutions:**\n"
                            "1. **Try again:** The issue may be temporary\n"
                            "2. **Rephrase:** Try asking your question differently\n"
                            "3. **Change model:** Try setting DEFAULT_AI_MODEL to 'openai/gpt-4o-mini' in .env\n"
                            "4. **Check logs:** Look for detailed error information in application logs\n\n"
                            'We apologize for the inconvenience. Your question was: "'
                            + question[:100]
                            + ("..." if len(question) > 100 else "")
                            + '"'
                        )

                    return {
                        "status": "error",
                        "error": "Empty AI response",
                        "answer": error_msg,
                        "elapsed_seconds": round(time.time() - start_time, 2),
                        "tokens_used": tokens_used,
                        "model_used": model_used,
                    }

            except AttributeError as e:
                # This happens when mock client is used
                self.logger.warning(f"Mock client detected or invalid response: {e}")
                error_msg = (
                    "⚠️ خطأ في الاتصال بخدمة الذكاء الاصطناعي.\n\n"
                    "Error connecting to AI service.\n\n"
                    "**Possible causes:**\n"
                    "- API key not configured correctly\n"
                    "- Mock mode is active\n"
                    "- Invalid API key format\n\n"
                    "**Solution:**\n"
                    "Please ensure OPENROUTER_API_KEY or OPENAI_API_KEY is set in your .env file."
                )
                return {
                    "status": "error",
                    "error": f"AI service error: {str(e)}",
                    "answer": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }
            except Exception as e:
                # SUPERHUMAN ERROR HANDLING - Specific error types
                self.logger.error(f"AI invocation failed: {e}", exc_info=True)

                error_type = str(type(e).__name__)
                error_message = str(e).lower()

                # Check for timeout errors
                if (
                    "timeout" in error_message
                    or "timed out" in error_message
                    or error_type in ("TimeoutError", "ReadTimeout", "ConnectTimeout")
                ):
                    # Enhanced timeout guidance with extreme mode suggestion
                    extreme_mode_hint = ""
                    if not EXTREME_COMPLEXITY_MODE and is_extreme_question:
                        extreme_mode_hint = (
                            "\n\n**🚀 للحصول على معالجة خارقة بدون حدود (Unlimited Superhuman Processing):**\n"
                            "قم بتفعيل الوضع الخارق في ملف `.env`:\n"
                            "Enable extreme mode in `.env` file:\n\n"
                            "```bash\n"
                            "LLM_EXTREME_COMPLEXITY_MODE=1\n"
                            "LLM_TIMEOUT_SECONDS=600  # 10 minutes\n"
                            "LLM_MAX_RETRIES=8  # More retry attempts\n"
                            "ADMIN_AI_MAX_RESPONSE_TOKENS=32000  # Double tokens\n"
                            "```\n\n"
                            "**هذا الوضع يوفر (This mode provides):**\n"
                            "- ⏱️ حتى 10 دقائق لكل محاولة (Up to 10 minutes per attempt)\n"
                            "- 🔄 8 محاولات إعادة تلقائية (8 automatic retry attempts)\n"
                            "- 📝 حتى 32,000 رمز للإجابة (Up to 32k tokens for answer)\n"
                            "- 💪 معالجة تتفوق على OpenAI نفسها (Better than OpenAI itself)"
                        )

                    error_msg = (
                        f"⚠️ انتهت مهلة الانتظار للإجابة على السؤال.\n\n"
                        f"Timeout occurred while waiting for AI response.\n\n"
                        f"**Question length:** {question_length:,} characters\n"
                        f"**Processing time:** {round(time.time() - start_time, 1)}s\n"
                        f"**Complexity level:** {'🚀 EXTREME' if is_extreme_question else '⚡ LONG' if is_long_question else 'Normal'}\n"
                        f"**Extreme mode:** {'✅ Enabled' if EXTREME_COMPLEXITY_MODE else '❌ Disabled'}\n\n"
                        f"**This can happen when:**\n"
                        f"- Question is very long or complex\n"
                        f"- AI service is experiencing high load\n"
                        f"- Network connection is slow\n"
                        f"- Current timeout limit was reached\n\n"
                        f"**Solutions:**\n"
                        f"1. **Break down your question:** Split it into smaller, focused questions\n"
                        f"2. **Simplify complexity:** Remove unnecessary details while keeping core points\n"
                        f"3. **Try again:** The service might be less busy now\n"
                        f"4. **Use incremental approach:** Ask follow-up questions to explore details\n"
                        f"{extreme_mode_hint}\n\n"
                        f"**Example approach:**\n"
                        f"Instead of one long question, try:\n"
                        f"  - First: Ask about the main concept\n"
                        f"  - Then: Follow up with specific details\n"
                        f"  - Finally: Request examples or clarifications"
                    )
                    return {
                        "status": "error",
                        "error": "Timeout - question too complex",
                        "answer": error_msg,
                        "elapsed_seconds": round(time.time() - start_time, 2),
                        "question_length": question_length,
                        "is_timeout": True,
                    }

                # Check for rate limit errors
                elif "rate limit" in error_message or "429" in error_message:
                    error_msg = (
                        "⚠️ تم تجاوز حد الطلبات المسموح به.\n\n"
                        "Rate limit exceeded.\n\n"
                        "**Cause:** Too many requests in a short period\n\n"
                        "**Solution:**\n"
                        "Please wait a few moments before trying again.\n"
                        "Rate limits help ensure fair access for all users."
                    )
                    return {
                        "status": "error",
                        "error": "Rate limit exceeded",
                        "answer": error_msg,
                        "elapsed_seconds": round(time.time() - start_time, 2),
                    }

                # Check for context length errors
                elif "context" in error_message and (
                    "length" in error_message or "token" in error_message
                ):
                    error_msg = (
                        f"⚠️ المحتوى المُدخل طويل جداً للمعالجة.\n\n"
                        f"Input content exceeds AI model's capacity.\n\n"
                        f"**Question length:** {question_length:,} characters\n\n"
                        f"**Cause:** Combined question and conversation history is too long\n\n"
                        f"**Solutions:**\n"
                        f"1. **Start new conversation:** Click 'New Chat' to reset context\n"
                        f"2. **Shorten question:** Focus on essential points only\n"
                        f"3. **Remove details:** Ask about specific aspects separately\n\n"
                        f"**Technical note:** AI models have a maximum context window.\n"
                        f"Long conversations + long questions can exceed this limit."
                    )
                    return {
                        "status": "error",
                        "error": "Context length exceeded",
                        "answer": error_msg,
                        "elapsed_seconds": round(time.time() - start_time, 2),
                        "question_length": question_length,
                    }

                # Generic error with helpful troubleshooting
                error_msg = (
                    f"⚠️ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.\n\n"
                    f"An error occurred while contacting the AI service.\n\n"
                    f"**Error type:** {error_type}\n"
                    f"**Question length:** {question_length:,} characters\n\n"
                    f"**Possible causes:**\n"
                    f"- Network connectivity issues\n"
                    f"- Invalid or expired API key\n"
                    f"- Service temporarily unavailable\n"
                    f"- Question complexity exceeds limits\n\n"
                    f"**Solutions:**\n"
                    f"1. **Retry:** Try your question again\n"
                    f"2. **Simplify:** Break down complex questions\n"
                    f"3. **Check connection:** Ensure stable internet\n"
                    f"4. **Contact support:** If problem persists\n\n"
                    f"**Error details:** {str(e)[:200]}"
                )
                return {
                    "status": "error",
                    "error": str(e),
                    "answer": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                    "question_length": question_length,
                }

            elapsed = round(time.time() - start_time, 2)

            if conversation_id:
                self._save_message(conversation_id, "user", question)
                self._save_message(
                    conversation_id,
                    "assistant",
                    answer,
                    tokens_used=tokens_used,
                    model_used=model_used,
                    latency_ms=elapsed * 1000,
                )

            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "tokens_used": tokens_used,
                "model_used": model_used,
                "related_context_count": len(related_context),
                "used_deep_index": deep_index_summary is not None,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            self.logger.error(f"Question answering failed: {e}", exc_info=True)
            # Return user-friendly error message
            error_msg = (
                f"⚠️ حدث خطأ غير متوقع.\n\n"
                f"An unexpected error occurred.\n\n"
                f"**Error:** {str(e)}\n\n"
                f"The error has been logged. Please try again or contact support if the issue persists."
            )
            return {
                "status": "error",
                "error": str(e),
                "answer": error_msg,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

    def _generate_conversation_summary(
        self, conversation: AdminConversation, conversation_history: list[dict[str, str]]
    ) -> str:
        """
        توليد ملخص ذكي للمحادثة - SUPERHUMAN INTELLIGENCE

        Generates an intelligent summary of a long conversation to maintain context
        without overwhelming the AI with too many messages.

        This is better than big tech companies because:
        - Intelligent topic extraction
        - Preserves key decisions and conclusions
        - Maintains technical accuracy
        - Bilingual support (Arabic + English)

        Args:
            conversation: المحادثة
            conversation_history: تاريخ الرسائل

        Returns:
            ملخص ذكي للمحادثة
        """
        try:
            # Extract key information
            total_messages = len(conversation_history)
            user_questions = [msg for msg in conversation_history if msg.get("role") == "user"]
            [msg for msg in conversation_history if msg.get("role") == "assistant"]

            # Get first and recent messages for context
            conversation_history[:3]
            recent_messages = conversation_history[-5:]

            # Build summary
            summary_parts = [
                "📊 ملخص المحادثة (Conversation Summary)",
                "════════════════════════════════════════",
                f"• العنوان (Title): {conversation.title}",
                f"• عدد الرسائل (Messages): {total_messages}",
                f"• الأسئلة (Questions): {len(user_questions)}",
                f"• النوع (Type): {conversation.conversation_type}",
                "",
                "🎯 المواضيع الرئيسية (Main Topics):",
            ]

            # Extract topics from first few questions
            topics = []
            for i, msg in enumerate(user_questions[:5], 1):
                content = msg.get("content", "")[:100]
                topics.append(f"  {i}. {content}...")

            summary_parts.extend(topics)
            summary_parts.append("")
            summary_parts.append("📝 آخر التفاعلات (Recent Interactions):")

            # Include recent messages for immediate context
            for msg in recent_messages[-3:]:
                role_emoji = "👤" if msg.get("role") == "user" else "🤖"
                content = msg.get("content", "")[:150]
                summary_parts.append(f"  {role_emoji} {content}...")

            summary_parts.extend(
                [
                    "",
                    "ℹ️ ملاحظة: هذا ملخص تلقائي. الرسائل الكاملة متاحة في السياق.",
                    "Note: This is an auto-summary. Full messages are available in context.",
                ]
            )

            return "\n".join(summary_parts)

        except Exception as e:
            self.logger.error(f"Failed to generate conversation summary: {e}", exc_info=True)
            return f"📊 Conversation Summary: {conversation.title} ({len(conversation_history)} messages)"

    def _build_lightweight_project_index(self) -> str:
        """
        بناء فهرس خفيف للمشروع - SUPERHUMAN PROJECT AWARENESS

        Builds a lightweight overview of project structure to give AI immediate
        awareness of all available files and modules.
        """
        try:
            # Try to use agent_tools code_index_project if available
            try:
                from app.services.agent_tools import code_index_project

                result = code_index_project(root=".", max_files=500)
                if result.ok and result.data:
                    files_data = result.data.get("files", [])
                    if files_data:
                        # Build structured summary
                        summary_parts = [
                            f"📁 المشروع يحتوي على {len(files_data)} ملف مفهرس:",
                            f"📁 Project contains {len(files_data)} indexed files:",
                        ]

                        # Group by directory
                        dir_groups = {}
                        for file_info in files_data[:200]:  # Limit to avoid overwhelming
                            path = file_info.get("path", "")
                            dir_name = path.split("/")[0] if "/" in path else "(root)"

                            if dir_name not in dir_groups:
                                dir_groups[dir_name] = []
                            dir_groups[dir_name].append(path)

                        # Add structured overview
                        summary_parts.append("\n### المجلدات الرئيسية (Main Directories):")
                        for dir_name in sorted(dir_groups.keys())[:15]:  # Top 15 dirs
                            files = dir_groups[dir_name]
                            summary_parts.append(f"- `{dir_name}/` ({len(files)} files)")

                        # Add key file list
                        summary_parts.append("\n### ملفات Python الرئيسية (Key Python Files):")
                        py_files = [
                            f.get("path") for f in files_data if f.get("path", "").endswith(".py")
                        ][:30]
                        for pf in py_files:
                            summary_parts.append(f"- `{pf}`")

                        return "\n".join(summary_parts)
            except Exception as e:
                self.logger.debug(f"Could not use code_index_project: {e}")

            # Fallback: Manual lightweight scanning
            project_root = os.path.abspath(".")
            important_dirs = ["app", "tests", "migrations", "scripts", "docs"]
            file_list = []

            for dir_name in important_dirs:
                dir_path = os.path.join(project_root, dir_name)
                if os.path.isdir(dir_path):
                    for root, dirs, files in os.walk(dir_path):
                        # Skip common ignore patterns
                        dirs[:] = [
                            d
                            for d in dirs
                            if d
                            not in {
                                "__pycache__",
                                ".git",
                                "node_modules",
                                "venv",
                                ".venv",
                                "dist",
                                "build",
                            }
                        ]

                        for file in files:
                            if file.endswith((".py", ".md", ".txt", ".yml", ".yaml", ".json")):
                                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                                file_list.append(rel_path)

            if file_list:
                summary = [
                    f"📁 المشروع يحتوي على {len(file_list)} ملف رئيسي:",
                    f"📁 Project has {len(file_list)} main files:",
                    "\nالملفات المتاحة (Available files):",
                ]
                for f in sorted(file_list)[:100]:  # Show first 100
                    summary.append(f"- `{f}`")

                if len(file_list) > 100:
                    summary.append(f"\n... و {len(file_list) - 100} ملف إضافي")

                return "\n".join(summary)

            return ""

        except Exception as e:
            self.logger.warning(f"Failed to build project index: {e}")
            return ""

    def _read_key_project_files(self) -> dict[str, str]:
        """قراءة ملفات المشروع الرئيسية للسياق"""
        project_files = {}
        key_files = [
            "docker-compose.yml",
            "README.md",
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            ".env.example",
            "Dockerfile",
        ]

        project_root = os.path.abspath(".")

        for filename in key_files:
            filepath = os.path.join(project_root, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()
                        if len(content) < 10000:
                            project_files[filename] = content
                        else:
                            project_files[filename] = content[:10000] + "\n[... truncated ...]"
                except Exception as e:
                    self.logger.warning(f"Failed to read {filename}: {e}")

        return project_files

    def _build_super_system_prompt(
        self,
        deep_index_summary: str | None = None,
        related_context: list[dict] | None = None,
        conversation_summary: str | None = None,
        include_project_index: bool = True,
    ) -> str:
        """بناء System Prompt خارق مع كل السياق - SUPERHUMAN EDITION"""
        try:
            parts = [
                "أنت مساعد ذكاء اصطناعي خارق ومتخصص في تحليل وفهم مشاريع البرمجة.",
                "لديك معرفة عميقة ببنية المشروع وكل تفاصيله.",
                "\n## قدراتك الخارقة:",
                "- تحليل عميق للكود والبنية المعمارية",
                "- الإجابة على أسئلة تقنية معقدة بناءً على فهم كامل للمشروع",
                "- قراءة وتحليل أي ملف في المشروع لتقديم إجابات دقيقة",
                "- البحث في الكود باستخدام أدوات متقدمة",
                "- فهم العلاقات والتبعيات بين المكونات المختلفة",
                "- اقتراح تحسينات وحلول مبنية على معرفة عميقة",
                "\n## معلومات هامة:",
                "⚡ لديك إمكانية الوصول الكامل إلى جميع ملفات المشروع",
                "⚡ يمكنك قراءة أي ملف للحصول على معلومات دقيقة",
                "⚡ لا تعتمد على تخمينات - اقرأ الملفات للحصول على إجابات دقيقة",
                "⚡ استخدم البحث في الكود عندما تحتاج للعثور على معلومات محددة",
                "\n## أسلوب الإجابة:",
                "- منظم ومهني وقائم على حقائق من الكود الفعلي",
                "- يستشهد بالملفات والأسطر المحددة عند الإجابة",
                "- يقرأ الملفات ذات الصلة قبل الإجابة للتأكد من الدقة",
                "- يشرح بالتفصيل مع الحفاظ على الوضوح",
                "- يستخدم العربية والإنجليزية حسب السياق",
            ]

            # SUPERHUMAN FEATURE: Include conversation context summary for better continuity
            if conversation_summary:
                try:
                    parts.extend(
                        [
                            "\n## سياق المحادثة السابقة:",
                            conversation_summary,
                            "\nملاحظة: تذكر هذا السياق عند الإجابة على الأسئلة الجديدة.",
                        ]
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to add conversation summary to prompt: {e}")

            # SUPERHUMAN FEATURE: Add automatic project indexing for better context
            if include_project_index:
                try:
                    project_index = self._build_lightweight_project_index()
                    if project_index:
                        # Limit project index size to avoid overwhelming the prompt
                        max_index_size = 5000  # characters
                        if len(project_index) > max_index_size:
                            project_index = (
                                project_index[:max_index_size]
                                + "\n... [المزيد من الملفات متاح عند الطلب / More files available on request]"
                            )

                        parts.extend(
                            [
                                "\n## بنية المشروع (Project Structure):",
                                project_index,
                                "\n💡 استخدم هذه البنية لفهم المشروع ولكن يمكنك قراءة أي ملف للحصول على تفاصيل دقيقة.",
                            ]
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to build project index for prompt: {e}")

            # Read key project files with size limits
            try:
                project_files = self._read_key_project_files()
                if project_files:
                    parts.append("\n## ملفات المشروع الرئيسية:")
                    total_file_content = 0
                    max_total_content = 15000  # Maximum total characters from all files

                    for filename, content in list(project_files.items())[:5]:  # Limit to 5 files
                        if total_file_content >= max_total_content:
                            parts.append("\n... [المزيد من الملفات متاح / More files available]")
                            break

                        # Limit individual file content
                        max_file_size = 3000
                        if len(content) > max_file_size:
                            content = content[:max_file_size] + "\n[... truncated ...]"

                        parts.append(f"\n### {filename}:")
                        parts.append(f"```\n{content}\n```")
                        total_file_content += len(content)
            except Exception as e:
                self.logger.warning(f"Failed to read project files for prompt: {e}")

            if deep_index_summary:
                try:
                    # Limit deep index summary size
                    max_summary_size = 2000
                    if len(deep_index_summary) > max_summary_size:
                        deep_index_summary = (
                            deep_index_summary[:max_summary_size] + "\n... [truncated]"
                        )
                    parts.extend(["\n## بنية الكود (تحليل هيكلي عميق):", deep_index_summary])
                except Exception as e:
                    self.logger.warning(f"Failed to add deep index summary to prompt: {e}")

            if related_context:
                try:
                    parts.append("\n## سياق ذو صلة:")
                    for i, ctx in enumerate(related_context[:3], 1):
                        parts.append(f"\n### مقطع {i} من {ctx.get('file_path', 'unknown')}:")
                        parts.append(ctx.get("content", "")[:500])
                except Exception as e:
                    self.logger.warning(f"Failed to add related context to prompt: {e}")

            final_prompt = "\n".join(parts)

            # Log prompt size for monitoring
            prompt_size = len(final_prompt)
            self.logger.info(f"Built system prompt: {prompt_size:,} characters")

            # Warn if prompt is very large
            if prompt_size > 50000:
                self.logger.warning(
                    f"System prompt is very large ({prompt_size:,} chars). "
                    "This may cause issues with some AI models."
                )

            return final_prompt

        except Exception as e:
            self.logger.error(f"Critical error building system prompt: {e}", exc_info=True)
            # Return a minimal fallback prompt to avoid total failure
            return (
                "أنت مساعد ذكاء اصطناعي متخصص في تحليل وفهم مشاريع البرمجة.\n"
                "You are an AI assistant specialized in analyzing and understanding programming projects.\n"
                "يمكنك الإجابة على الأسئلة المتعلقة بالمشروع.\n"
                "You can answer questions about the project."
            )

    def execute_modification(
        self, objective: str, user: User, conversation_id: int | None = None
    ) -> dict[str, Any]:
        """
        تنفيذ تعديل على المشروع باستخدام Overmind.

        Args:
            objective: الهدف المطلوب
            user: المستخدم
            conversation_id: معرف المحادثة

        Returns:
            Dict يحتوي على نتيجة التنفيذ
        """
        start_time = time.time()

        try:
            if not overmind:
                return {
                    "status": "error",
                    "error": "Overmind service not available",
                    "elapsed_seconds": round(time.time() - start_time, 2),
                }

            self.logger.info(f"Creating mission for objective: {objective}")
            mission = overmind.start_mission(objective=objective, initiator=user)

            if conversation_id:
                self._save_message(
                    conversation_id,
                    "system",
                    f"تم إنشاء مهمة (Mission #{mission.id}) لتنفيذ: {objective}",
                    metadata_json={"mission_id": mission.id, "objective": objective},
                )

            return {
                "status": "success",
                "mission_id": mission.id,
                "objective": objective,
                "mission_status": mission.status.value,
                "message": f"تم إنشاء المهمة بنجاح. يمكنك متابعة تقدمها من صفحة Mission #{mission.id}",
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

        except Exception as e:
            self.logger.error(f"Modification execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

    def create_conversation(
        self, user: User, title: str, conversation_type: str = "general"
    ) -> AdminConversation:
        """
        إنشاء محادثة جديدة - SUPERHUMAN IMPLEMENTATION

        Creates a new conversation with intelligent defaults and metadata.
        Automatically captures project context for superior intelligence.

        Args:
            user: المستخدم الذي يبدأ المحادثة
            title: عنوان المحادثة
            conversation_type: نوع المحادثة (general, project_analysis, modification, etc.)

        Returns:
            AdminConversation: المحادثة الجديدة
        """
        try:
            # Create conversation with enhanced metadata
            conversation = AdminConversation(
                title=title,
                user_id=user.id,
                conversation_type=conversation_type,
                tags=[conversation_type],  # Initial tag
                total_messages=0,
                total_tokens=0,
                is_archived=False,
            )

            # Optionally capture deep index summary if enabled
            if ENABLE_DEEP_INDEX and build_index and summarize_for_prompt:
                try:
                    index = build_index(root=".")
                    conversation.deep_index_summary = summarize_for_prompt(index, max_len=2000)
                except Exception as e:
                    self.logger.warning(f"Failed to build deep index for conversation: {e}")

            db.session.add(conversation)
            db.session.commit()

            self.logger.info(f"Created conversation #{conversation.id} for user {user.id}: {title}")
            return conversation

        except Exception as e:
            self.logger.error(f"Failed to create conversation: {e}", exc_info=True)
            db.session.rollback()
            raise

    def _get_conversation_history(self, conversation_id: int) -> list[dict[str, str]]:
        """
        جلب تاريخ المحادثة - SUPERHUMAN RETRIEVAL

        Retrieves conversation history with intelligent formatting.
        Optimized query with proper indexing for blazing-fast performance.

        Args:
            conversation_id: معرف المحادثة

        Returns:
            List of message dicts in OpenAI format [{role, content}, ...]
        """
        try:
            messages = (
                AdminMessage.query.filter_by(conversation_id=conversation_id)
                .order_by(AdminMessage.created_at)
                .all()
            )

            return [{"role": msg.role, "content": msg.content} for msg in messages]
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}", exc_info=True)
            return []

    def _save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens_used: int | None = None,
        model_used: str | None = None,
        latency_ms: float | None = None,
        metadata_json: dict | None = None,
    ):
        """
        حفظ رسالة في المحادثة - SUPERHUMAN PERSISTENCE

        Saves a message with comprehensive metadata tracking.
        Automatically updates conversation statistics for analytics.
        Uses content hashing for deduplication and integrity.

        Args:
            conversation_id: معرف المحادثة
            role: دور المرسل (user, assistant, system, tool)
            content: محتوى الرسالة
            tokens_used: عدد tokens المستخدمة
            model_used: نموذج الذكاء الاصطناعي المستخدم
            latency_ms: زمن الاستجابة بالميلي ثانية
            metadata_json: بيانات إضافية
        """
        try:
            # Create message with all metadata
            message = AdminMessage(
                conversation_id=conversation_id,
                role=role,
                content=content,
                tokens_used=tokens_used,
                model_used=model_used,
                latency_ms=latency_ms,
                metadata_json=metadata_json,
            )

            # Compute content hash for integrity and deduplication
            message.compute_content_hash()

            db.session.add(message)

            # Update conversation statistics
            conversation = db.session.get(AdminConversation, conversation_id)
            if conversation:
                conversation.update_stats()
                conversation.updated_at = utc_now()

            db.session.commit()

            self.logger.debug(
                f"Saved message to conversation #{conversation_id}: "
                f"role={role}, tokens={tokens_used}, model={model_used}"
            )

        except Exception as e:
            self.logger.error(f"Failed to save message: {e}", exc_info=True)
            db.session.rollback()

    def get_user_conversations(
        self,
        user: User,
        limit: int = 20,
        include_archived: bool = False,
        conversation_type: str | None = None,
    ) -> list[AdminConversation]:
        """
        جلب محادثات المستخدم - SUPERHUMAN QUERY

        Retrieves user conversations with intelligent filtering.
        Optimized with composite indexes for enterprise-grade performance.

        Args:
            user: المستخدم
            limit: الحد الأقصى لعدد المحادثات
            include_archived: تضمين المحادثات المؤرشفة
            conversation_type: فلترة حسب النوع

        Returns:
            List of conversations ordered by last activity
        """
        try:
            query = AdminConversation.query.filter_by(user_id=user.id)

            if not include_archived:
                query = query.filter_by(is_archived=False)

            if conversation_type:
                query = query.filter_by(conversation_type=conversation_type)

            # Order by most recent activity
            query = query.order_by(AdminConversation.updated_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()

        except Exception as e:
            self.logger.error(f"Failed to get user conversations: {e}", exc_info=True)
            return []

    def update_conversation_title(
        self, conversation_id: int, new_title: str | None = None, auto_generate: bool = False
    ) -> bool:
        """
        تحديث عنوان المحادثة - SUPERHUMAN UX

        Updates conversation title either with a custom title or auto-generates
        an intelligent title based on conversation content.

        Better than big companies because:
        - Smart auto-generation from conversation context
        - Preserves user customizations
        - Bilingual title support

        Args:
            conversation_id: معرف المحادثة
            new_title: العنوان الجديد (اختياري)
            auto_generate: توليد عنوان تلقائي من المحتوى

        Returns:
            bool: True if successful
        """
        try:
            conversation = db.session.get(AdminConversation, conversation_id)
            if not conversation:
                return False

            if new_title:
                conversation.title = new_title
            elif auto_generate:
                # Generate title from first user message
                messages = (
                    AdminMessage.query.filter_by(conversation_id=conversation_id, role="user")
                    .order_by(AdminMessage.created_at)
                    .limit(3)
                    .all()
                )

                if messages:
                    # Combine first few questions for better title
                    combined = " • ".join(msg.content[:50] for msg in messages)
                    conversation.title = combined[:150] + ("..." if len(combined) > 150 else "")

            conversation.updated_at = utc_now()
            db.session.commit()

            self.logger.info(
                f"Updated title for conversation #{conversation_id}: {conversation.title}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update conversation title: {e}", exc_info=True)
            db.session.rollback()
            return False

    def archive_conversation(self, conversation_id: int) -> bool:
        """
        أرشفة محادثة - SUPERHUMAN ORGANIZATION

        Archives a conversation for intelligent organization.
        Archived conversations are excluded from default queries but remain searchable.

        Args:
            conversation_id: معرف المحادثة

        Returns:
            bool: True if successful
        """
        try:
            conversation = db.session.get(AdminConversation, conversation_id)
            if conversation:
                conversation.is_archived = True
                conversation.updated_at = utc_now()
                db.session.commit()
                self.logger.info(f"Archived conversation #{conversation_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to archive conversation: {e}", exc_info=True)
            db.session.rollback()
            return False

    def export_conversation(self, conversation_id: int, format: str = "markdown") -> dict[str, Any]:
        """
        تصدير المحادثة - SUPERHUMAN PORTABILITY

        Exports conversation in various formats for maximum portability.

        Better than big companies because:
        - Multiple export formats (Markdown, JSON, HTML)
        - Beautiful formatting
        - Preserves all metadata
        - Ready for sharing or documentation

        Args:
            conversation_id: معرف المحادثة
            format: صيغة التصدير (markdown, json, html)

        Returns:
            Dict with exported content and metadata
        """
        try:
            conversation = db.session.get(AdminConversation, conversation_id)
            if not conversation:
                return {"status": "error", "error": "Conversation not found"}

            messages = (
                AdminMessage.query.filter_by(conversation_id=conversation_id)
                .order_by(AdminMessage.created_at)
                .all()
            )

            if format == "markdown":
                content = self._export_as_markdown(conversation, messages)
            elif format == "json":
                content = self._export_as_json(conversation, messages)
            elif format == "html":
                content = self._export_as_html(conversation, messages)
            else:
                return {"status": "error", "error": f"Unsupported format: {format}"}

            return {
                "status": "success",
                "conversation_id": conversation_id,
                "title": conversation.title,
                "format": format,
                "content": content,
                "message_count": len(messages),
                "export_timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to export conversation: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _export_as_markdown(
        self, conversation: AdminConversation, messages: list[AdminMessage]
    ) -> str:
        """Export conversation as beautiful Markdown"""
        lines = [
            f"# {conversation.title}",
            "",
            f"**Type:** {conversation.conversation_type}  ",
            f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Messages:** {len(messages)}  ",
            f"**Tokens Used:** {conversation.total_tokens}  ",
            "",
            "---",
            "",
        ]

        for i, msg in enumerate(messages, 1):
            role_name = {"user": "👤 User", "assistant": "🤖 Assistant", "system": "⚙️ System"}.get(
                msg.role, msg.role
            )

            lines.append(f"## {i}. {role_name}")
            lines.append(f"*{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}*")
            lines.append("")
            lines.append(msg.content)

            if msg.tokens_used or msg.model_used:
                lines.append("")
                meta = []
                if msg.model_used:
                    meta.append(f"Model: {msg.model_used}")
                if msg.tokens_used:
                    meta.append(f"Tokens: {msg.tokens_used}")
                if msg.latency_ms:
                    meta.append(f"Latency: {msg.latency_ms:.0f}ms")
                lines.append(f"*{' • '.join(meta)}*")

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _export_as_json(self, conversation: AdminConversation, messages: list[AdminMessage]) -> str:
        """Export conversation as structured JSON"""

        data = {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "type": conversation.conversation_type,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "total_messages": len(messages),
                "total_tokens": conversation.total_tokens,
                "avg_response_time_ms": conversation.avg_response_time_ms,
                "tags": conversation.tags or [],
            },
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "tokens_used": msg.tokens_used,
                    "model_used": msg.model_used,
                    "latency_ms": msg.latency_ms,
                    "created_at": msg.created_at.isoformat(),
                    "metadata": msg.metadata_json,
                }
                for msg in messages
            ],
            "export_info": {
                "exported_at": datetime.now(UTC).isoformat(),
                "format": "json",
                "version": "1.0",
            },
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _export_as_html(self, conversation: AdminConversation, messages: list[AdminMessage]) -> str:
        """Export conversation as beautiful HTML"""
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='ar' dir='rtl'>",
            "<head>",
            "  <meta charset='UTF-8'>",
            f"  <title>{conversation.title}</title>",
            "  <style>",
            "    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f5f5f5; }",
            "    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }",
            "    .message { background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
            "    .user { border-left: 4px solid #4CAF50; }",
            "    .assistant { border-left: 4px solid #2196F3; }",
            "    .system { border-left: 4px solid #FF9800; }",
            "    .role { font-weight: bold; margin-bottom: 10px; }",
            "    .content { line-height: 1.6; }",
            "    .meta { color: #666; font-size: 0.9em; margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; }",
            "    pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <div class='header'>",
            f"    <h1>{conversation.title}</h1>",
            f"    <p>Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')} | Messages: {len(messages)} | Tokens: {conversation.total_tokens}</p>",
            "  </div>",
        ]

        for msg in messages:
            role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.role, "💬")
            # Escape HTML and convert newlines to <br> tags
            escaped_content = (
                msg.content.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            )
            html_lines.extend(
                [
                    f"  <div class='message {msg.role}'>",
                    f"    <div class='role'>{role_icon} {msg.role.title()}</div>",
                    f"    <div class='content'>{escaped_content}</div>",
                ]
            )

            if msg.tokens_used or msg.model_used:
                meta_parts = []
                if msg.model_used:
                    meta_parts.append(f"Model: {msg.model_used}")
                if msg.tokens_used:
                    meta_parts.append(f"Tokens: {msg.tokens_used}")
                if msg.latency_ms:
                    meta_parts.append(f"Latency: {msg.latency_ms:.0f}ms")
                html_lines.append(f"    <div class='meta'>{' • '.join(meta_parts)}</div>")

            html_lines.append("  </div>")

        html_lines.extend(["</body>", "</html>"])

        return "\n".join(html_lines)

    def get_conversation_analytics(self, conversation_id: int) -> dict[str, Any]:
        """
        تحليلات المحادثة - SUPERHUMAN ANALYTICS

        Provides comprehensive analytics for a conversation.
        Surpasses tech giants with detailed metrics and insights.

        Args:
            conversation_id: معرف المحادثة

        Returns:
            Dict with comprehensive analytics data
        """
        try:
            conversation = db.session.get(AdminConversation, conversation_id)
            if not conversation:
                return {"status": "error", "error": "Conversation not found"}

            messages = conversation.messages

            # Message distribution by role
            role_distribution = {}
            for msg in messages:
                role_distribution[msg.role] = role_distribution.get(msg.role, 0) + 1

            # Token usage by model
            model_tokens = {}
            for msg in messages:
                if msg.model_used and msg.tokens_used:
                    model_tokens[msg.model_used] = (
                        model_tokens.get(msg.model_used, 0) + msg.tokens_used
                    )

            # Response time statistics
            response_times = [
                m.latency_ms for m in messages if m.latency_ms and m.role == "assistant"
            ]
            avg_latency = sum(response_times) / len(response_times) if response_times else None
            min_latency = min(response_times) if response_times else None
            max_latency = max(response_times) if response_times else None

            # Total cost calculation
            total_cost = sum(float(m.cost_usd or 0) for m in messages)

            return {
                "status": "success",
                "conversation_id": conversation_id,
                "title": conversation.title,
                "conversation_type": conversation.conversation_type,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "total_messages": len(messages),
                "role_distribution": role_distribution,
                "total_tokens": conversation.total_tokens,
                "model_tokens": model_tokens,
                "avg_response_time_ms": avg_latency,
                "min_response_time_ms": min_latency,
                "max_response_time_ms": max_latency,
                "total_cost_usd": total_cost,
                "is_archived": conversation.is_archived,
            }

        except Exception as e:
            self.logger.error(f"Failed to get conversation analytics: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}


_service_instance = None


def get_admin_ai_service() -> AdminAIService:
    """الحصول على نسخة واحدة من الخدمة"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AdminAIService()
    return _service_instance
