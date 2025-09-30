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
from datetime import datetime

from flask import current_app, has_app_context
from sqlalchemy import select, desc

from app import db
from app.models import (
    User, AdminConversation, AdminMessage,
    Mission, MissionStatus, utc_now
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
                    "timestamp": datetime.utcnow().isoformat(),
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
        """حفظ التحليل في المحادثة"""
        try:
            conv = db.session.get(AdminConversation, conversation_id)
            if conv:
                conv.deep_index_summary = analysis.get("deep_index_summary")
                conv.context_snapshot = {
                    "project_stats": analysis.get("project_stats"),
                    "architecture": analysis.get("architecture"),
                    "timestamp": analysis.get("timestamp")
                }
                db.session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save analysis to conversation: {e}")
    
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
                conv = db.session.get(AdminConversation, conversation_id)
                if conv and conv.deep_index_summary:
                    deep_index_summary = conv.deep_index_summary
            
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
        
        if deep_index_summary:
            parts.extend([
                "\n## بنية المشروع:",
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
        """إنشاء محادثة جديدة"""
        conv = AdminConversation(
            title=title,
            user_id=user.id,
            conversation_type=conversation_type
        )
        db.session.add(conv)
        db.session.commit()
        return conv
    
    def _get_conversation_history(self, conversation_id: int) -> List[Dict[str, str]]:
        """جلب تاريخ المحادثة"""
        messages = db.session.scalars(
            select(AdminMessage)
            .where(AdminMessage.conversation_id == conversation_id)
            .order_by(AdminMessage.created_at)
        ).all()
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
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
        """حفظ رسالة في المحادثة"""
        msg = AdminMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model_used=model_used,
            latency_ms=latency_ms,
            metadata_json=metadata_json
        )
        db.session.add(msg)
        db.session.commit()
    
    def get_user_conversations(
        self,
        user: User,
        limit: int = 20
    ) -> List[AdminConversation]:
        """جلب محادثات المستخدم"""
        return db.session.scalars(
            select(AdminConversation)
            .where(AdminConversation.user_id == user.id)
            .order_by(desc(AdminConversation.updated_at))
            .limit(limit)
        ).all()


_service_instance = None

def get_admin_ai_service() -> AdminAIService:
    """الحصول على نسخة واحدة من الخدمة"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AdminAIService()
    return _service_instance
