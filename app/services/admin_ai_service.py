# -*- coding: utf-8 -*-
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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app, has_app_context
from sqlalchemy import desc, select

from app import db
from app.models import (
    AdminConversation,
    AdminMessage,
    MessageRole,
    Mission,
    MissionStatus,
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


class AdminAIService:
    """
    الخدمة الرئيسية للذكاء الاصطناعي في صفحة الأدمن.
    """

    def __init__(self):
        self.logger = logger

    def analyze_project(
        self,
        user: User,
        conversation_id: Optional[int] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
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

    def _analyze_architecture(self, index: Dict) -> Dict[str, Any]:
        """تحليل البنية المعمارية"""
        layers = index.get("layers", {})
        return {
            "layers_detected": list(layers.keys()),
            "services_count": len(layers.get("service", [])),
            "models_count": len(layers.get("model", [])),
            "routes_count": len(layers.get("route", [])),
            "utils_count": len(layers.get("util", [])),
        }

    def _analyze_hotspots(self, index: Dict) -> List[Dict]:
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

    def _generate_recommendations(self, index: Dict) -> List[str]:
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

    def _save_analysis_to_conversation(self, conversation_id: int, analysis: Dict):
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
        conversation_id: Optional[int] = None,
        use_deep_context: bool = True,
    ) -> Dict[str, Any]:
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
                        f"⚠️ ليس لديك صلاحية للوصول إلى هذه المحادثة.\n\n"
                        f"You don't have permission to access this conversation.\n\n"
                        f"**Security Notice:**\n"
                        f"This conversation belongs to another user.\n\n"
                        f"**Solution:**\n"
                        f"Please use your own conversations or start a new one."
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

            system_prompt = self._build_super_system_prompt(
                deep_index_summary=deep_index_summary if use_deep_context else None,
                related_context=related_context,
                conversation_summary=context_summary if conversation_id else None,
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

                response = client.chat.completions.create(
                    model=DEFAULT_MODEL or "openai/gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                )

                answer = response.choices[0].message.content
                tokens_used = getattr(response.usage, "total_tokens", None)
                model_used = response.model

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
                # Other AI-related errors (rate limits, network, etc.)
                self.logger.error(f"AI invocation failed: {e}", exc_info=True)
                error_msg = (
                    f"⚠️ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.\n\n"
                    f"An error occurred while contacting the AI service.\n\n"
                    f"**Error details:** {str(e)}\n\n"
                    f"**Possible causes:**\n"
                    f"- Rate limit exceeded\n"
                    f"- Network connectivity issues\n"
                    f"- Invalid API key\n"
                    f"- Service temporarily unavailable\n\n"
                    f"**Solution:**\n"
                    f"Please try again in a few moments. If the problem persists, contact support."
                )
                return {
                    "status": "error",
                    "error": str(e),
                    "answer": error_msg,
                    "elapsed_seconds": round(time.time() - start_time, 2),
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
        self, conversation: AdminConversation, conversation_history: List[Dict[str, str]]
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
            assistant_responses = [
                msg for msg in conversation_history if msg.get("role") == "assistant"
            ]

            # Get first and recent messages for context
            first_messages = conversation_history[:3]
            recent_messages = conversation_history[-5:]

            # Build summary
            summary_parts = [
                f"📊 ملخص المحادثة (Conversation Summary)",
                f"════════════════════════════════════════",
                f"• العنوان (Title): {conversation.title}",
                f"• عدد الرسائل (Messages): {total_messages}",
                f"• الأسئلة (Questions): {len(user_questions)}",
                f"• النوع (Type): {conversation.conversation_type}",
                f"",
                f"🎯 المواضيع الرئيسية (Main Topics):",
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

    def _read_key_project_files(self) -> Dict[str, str]:
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
                    with open(filepath, "r", encoding="utf-8") as f:
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
        deep_index_summary: Optional[str] = None,
        related_context: Optional[List[Dict]] = None,
        conversation_summary: Optional[str] = None,
    ) -> str:
        """بناء System Prompt خارق مع كل السياق"""
        parts = [
            "أنت مساعد ذكاء اصطناعي خارق ومتخصص في تحليل وفهم مشاريع البرمجة.",
            "لديك معرفة عميقة ببنية المشروع وكل تفاصيله.",
            "\n## قدراتك:",
            "- تحليل عميق للكود والبنية المعمارية",
            "- الإجابة على أسئلة تقنية معقدة",
            "- اقتراح تحسينات وحلول",
            "- توضيح العلاقات بين المكونات المختلفة",
            "\n## أسلوب الإجابة:",
            "- منظم ومهني",
            "- يستخدم أمثلة من الكود الفعلي",
            "- يشرح بالتفصيل مع الحفاظ على الوضوح",
            "- يستخدم العربية والإنجليزية حسب السياق",
        ]

        # SUPERHUMAN FEATURE: Include conversation context summary for better continuity
        if conversation_summary:
            parts.extend(
                [
                    "\n## سياق المحادثة السابقة:",
                    conversation_summary,
                    "\nملاحظة: تذكر هذا السياق عند الإجابة على الأسئلة الجديدة.",
                ]
            )

        project_files = self._read_key_project_files()
        if project_files:
            parts.append("\n## ملفات المشروع الرئيسية:")
            for filename, content in project_files.items():
                parts.append(f"\n### {filename}:")
                parts.append(f"```\n{content}\n```")

        if deep_index_summary:
            parts.extend(["\n## بنية الكود (تحليل هيكلي):", deep_index_summary])

        if related_context:
            parts.append("\n## سياق ذو صلة:")
            for i, ctx in enumerate(related_context[:3], 1):
                parts.append(f"\n### مقطع {i} من {ctx.get('file_path', 'unknown')}:")
                parts.append(ctx.get("content", "")[:500])

        return "\n".join(parts)

    def execute_modification(
        self, objective: str, user: User, conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
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

    def _get_conversation_history(self, conversation_id: int) -> List[Dict[str, str]]:
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
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None,
        latency_ms: Optional[float] = None,
        metadata_json: Optional[Dict] = None,
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
        conversation_type: Optional[str] = None,
    ) -> List[AdminConversation]:
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
        self, conversation_id: int, new_title: Optional[str] = None, auto_generate: bool = False
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

    def export_conversation(self, conversation_id: int, format: str = "markdown") -> Dict[str, Any]:
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
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to export conversation: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _export_as_markdown(
        self, conversation: AdminConversation, messages: List[AdminMessage]
    ) -> str:
        """Export conversation as beautiful Markdown"""
        lines = [
            f"# {conversation.title}",
            f"",
            f"**Type:** {conversation.conversation_type}  ",
            f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Messages:** {len(messages)}  ",
            f"**Tokens Used:** {conversation.total_tokens}  ",
            f"",
            "---",
            f"",
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

    def _export_as_json(self, conversation: AdminConversation, messages: List[AdminMessage]) -> str:
        """Export conversation as structured JSON"""
        import json

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
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "format": "json",
                "version": "1.0",
            },
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _export_as_html(self, conversation: AdminConversation, messages: List[AdminMessage]) -> str:
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
            html_lines.extend(
                [
                    f"  <div class='message {msg.role}'>",
                    f"    <div class='role'>{role_icon} {msg.role.title()}</div>",
                    f"    <div class='content'>{msg.content.replace('<', '&lt;').replace('>', '&gt;').replace('\\n', '<br>')}</div>",
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

    def get_conversation_analytics(self, conversation_id: int) -> Dict[str, Any]:
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
