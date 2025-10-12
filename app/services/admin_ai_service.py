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
import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from flask import current_app, has_app_context
from sqlalchemy import select, desc

from app import db
from app.models import (
    User,
    Mission, MissionStatus, utc_now,
    AdminConversation, AdminMessage, MessageRole
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
        focus_areas: Optional[List[str]] = None
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
            if build_index and ENABLE_DEEP_INDEX:
                self.logger.info(f"Building deep index for project analysis (user_id={user.id})")
                index = build_index(root=".")
                
                analysis = {
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": user.id,
                    "project_stats": {
                        "files_scanned": index.get("files_scanned", 0),
                        "total_functions": index.get("global_metrics", {}).get("total_functions", 0),
                        "total_classes": len([c for m in index.get("modules", []) for c in m.get("classes", [])]),
                        "complexity_hotspots": len(index.get("complexity_hotspots_top50", [])),
                        "duplicate_functions": len(index.get("duplicate_function_bodies", {})),
                    },
                    "architecture": self._analyze_architecture(index),
                    "hotspots": self._analyze_hotspots(index),
                    "recommendations": self._generate_recommendations(index),
                    "deep_index_summary": summarize_for_prompt(index, max_len=3000) if summarize_for_prompt else None,
                    "full_index": index,
                    "elapsed_seconds": round(time.time() - start_time, 2)
                }
                
                if conversation_id:
                    self._save_analysis_to_conversation(conversation_id, analysis)
                
                return analysis
            else:
                return {
                    "status": "error",
                    "error": "Deep indexer not available",
                    "elapsed_seconds": round(time.time() - start_time, 2)
                }
                
        except Exception as e:
            self.logger.error(f"Project analysis failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2)
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
                    metadata_json={"analysis": analysis}
                )
                
                # Add 'analysis' tag
                if conversation.tags and 'analysis' not in conversation.tags:
                    conversation.tags.append('analysis')
                
                db.session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save analysis to conversation: {e}", exc_info=True)
    
    def answer_question(
        self,
        question: str,
        user: User,
        conversation_id: Optional[int] = None,
        use_deep_context: bool = True
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
            conversation_history = []
            deep_index_summary = None
            
            if conversation_id:
                conversation_history = self._get_conversation_history(conversation_id)
                # Get deep index summary from conversation if available
                conversation = db.session.get(AdminConversation, conversation_id)
                if conversation:
                    deep_index_summary = conversation.deep_index_summary
            
            related_context = []
            if system_service and hasattr(system_service, 'find_related_context'):
                try:
                    ctx_result = system_service.find_related_context(
                        question, 
                        limit=MAX_RELATED_CONTEXT_CHUNKS
                    )
                    if ctx_result.ok:
                        related_context = ctx_result.data.get("results", [])
                except Exception as e:
                    self.logger.warning(f"Failed to get related context: {e}")
            
            system_prompt = self._build_super_system_prompt(
                deep_index_summary=deep_index_summary if use_deep_context else None,
                related_context=related_context
            )
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history[-MAX_CONTEXT_MESSAGES:])
            messages.append({"role": "user", "content": question})
            
            if get_llm_client:
                client = get_llm_client()
                response = client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                answer = response.choices[0].message.content
                tokens_used = getattr(response.usage, 'total_tokens', None)
                model_used = response.model
                
            else:
                answer = "خدمة الذكاء الاصطناعي غير متاحة حالياً."
                tokens_used = None
                model_used = None
            
            elapsed = round(time.time() - start_time, 2)
            
            if conversation_id:
                self._save_message(conversation_id, "user", question)
                self._save_message(
                    conversation_id, 
                    "assistant", 
                    answer,
                    tokens_used=tokens_used,
                    model_used=model_used,
                    latency_ms=elapsed * 1000
                )
            
            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "tokens_used": tokens_used,
                "model_used": model_used,
                "related_context_count": len(related_context),
                "used_deep_index": deep_index_summary is not None,
                "elapsed_seconds": elapsed
            }
            
        except Exception as e:
            self.logger.error(f"Question answering failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2)
            }
    
    def _read_key_project_files(self) -> Dict[str, str]:
        """قراءة ملفات المشروع الرئيسية للسياق"""
        project_files = {}
        key_files = [
            'docker-compose.yml',
            'README.md',
            'requirements.txt',
            'pyproject.toml',
            'package.json',
            '.env.example',
            'Dockerfile'
        ]
        
        project_root = os.path.abspath('.')
        
        for filename in key_files:
            filepath = os.path.join(project_root, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
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
        related_context: Optional[List[Dict]] = None
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
        
        project_files = self._read_key_project_files()
        if project_files:
            parts.append("\n## ملفات المشروع الرئيسية:")
            for filename, content in project_files.items():
                parts.append(f"\n### {filename}:")
                parts.append(f"```\n{content}\n```")
        
        if deep_index_summary:
            parts.extend([
                "\n## بنية الكود (تحليل هيكلي):",
                deep_index_summary
            ])
        
        if related_context:
            parts.append("\n## سياق ذو صلة:")
            for i, ctx in enumerate(related_context[:3], 1):
                parts.append(f"\n### مقطع {i} من {ctx.get('file_path', 'unknown')}:")
                parts.append(ctx.get('content', '')[:500])
        
        return "\n".join(parts)
    
    def execute_modification(
        self,
        objective: str,
        user: User,
        conversation_id: Optional[int] = None
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
                    "elapsed_seconds": round(time.time() - start_time, 2)
                }
            
            self.logger.info(f"Creating mission for objective: {objective}")
            mission = overmind.start_mission(objective=objective, initiator=user)
            
            if conversation_id:
                self._save_message(
                    conversation_id,
                    "system",
                    f"تم إنشاء مهمة (Mission #{mission.id}) لتنفيذ: {objective}",
                    metadata_json={"mission_id": mission.id, "objective": objective}
                )
            
            return {
                "status": "success",
                "mission_id": mission.id,
                "objective": objective,
                "mission_status": mission.status.value,
                "message": f"تم إنشاء المهمة بنجاح. يمكنك متابعة تقدمها من صفحة Mission #{mission.id}",
                "elapsed_seconds": round(time.time() - start_time, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Modification execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2)
            }
    
    def create_conversation(
        self,
        user: User,
        title: str,
        conversation_type: str = "general"
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
                is_archived=False
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
            messages = AdminMessage.query.filter_by(
                conversation_id=conversation_id
            ).order_by(AdminMessage.created_at).all()
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in messages
            ]
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
        metadata_json: Optional[Dict] = None
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
                metadata_json=metadata_json
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
        conversation_type: Optional[str] = None
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
                    model_tokens[msg.model_used] = model_tokens.get(msg.model_used, 0) + msg.tokens_used
            
            # Response time statistics
            response_times = [m.latency_ms for m in messages if m.latency_ms and m.role == "assistant"]
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
                "is_archived": conversation.is_archived
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
