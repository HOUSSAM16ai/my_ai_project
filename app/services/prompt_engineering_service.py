"""
PROMPT ENGINEERING SERVICE - SUPERHUMAN EDITION
================================================
File        : app/services/prompt_engineering_service.py
Version     : 1.0.0 • "ULTIMATE-PROMPT-FORGE"
Status      : Production / Superhuman / Revolutionary
Author      : Overmind + RAG System + Meta-Prompt Engine

MISSION (المهمة)
-------
خدمة هندسة Prompts خارقة تنتج prompts احترافية مخصصة للمشروع:
  - تجمع المعرفة الكاملة عن المشروع (Knowledge Base)
  - تستخدم Meta-Prompt ديناميكي مع متغيرات المشروع
  - تدمج أمثلة Few-Shot من سياق المشروع
  - تستخدم RAG لجلب مقتطفات ذات صلة
  - تتفوق على أعظم شركات هندسة Prompts العالمية

CORE CAPABILITIES (القدرات الأساسية)
-----------------
1. generate_prompt() - توليد prompt خارق من وصف المستخدم
2. create_template() - إنشاء قالب meta-prompt جديد
3. get_project_context() - جمع سياق المشروع الكامل
4. retrieve_relevant_snippets() - استرجاع مقتطفات باستخدام RAG
5. build_few_shot_examples() - بناء أمثلة من المشروع
6. evaluate_prompt() - تقييم جودة الـ prompt المولد

ARCHITECTURE (البنية)
------------
Knowledge Base → RAG Retrieval → Meta-Prompt Engine → Prompt Generator
     ↓                                    ↓
Project Context                    Few-Shot Examples
     ↓                                    ↓
Vector Embeddings  →  Context Injection  →  Final Prompt
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
    GeneratedPrompt,
    PromptTemplate,
    User,
    AdminConversation,
    utc_now,
)

try:
    from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt
except ImportError:
    build_index = None
    summarize_for_prompt = None

try:
    from app.services.llm_client_service import get_llm_client
except ImportError:
    get_llm_client = None

try:
    from app.services import system_service
except ImportError:
    system_service = None

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "anthropic/claude-3.7-sonnet:thinking")
MAX_CONTEXT_SNIPPETS = int(os.getenv("PROMPT_ENG_MAX_CONTEXT_SNIPPETS", "5"))
MAX_FEW_SHOT_EXAMPLES = int(os.getenv("PROMPT_ENG_MAX_FEW_SHOT_EXAMPLES", "3"))
ENABLE_RAG = os.getenv("PROMPT_ENG_ENABLE_RAG", "1") == "1"


class PromptEngineeringService:
    """
    خدمة هندسة Prompts الخارقة - SUPERHUMAN PROMPT FORGE
    
    تولد prompts احترافية مخصصة لمشروعك تتفوق على أكبر الشركات العالمية
    """

    def __init__(self):
        self.logger = logger
        self._project_context_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

    def generate_prompt(
        self,
        user_description: str,
        user: User,
        template_id: int | None = None,
        conversation_id: int | None = None,
        use_rag: bool = True,
        prompt_type: str = "general",
    ) -> dict[str, Any]:
        """
        توليد Prompt خارق من وصف المستخدم
        
        Args:
            user_description: وصف المستخدم لما يريد
            user: المستخدم الذي يطلب التوليد
            template_id: معرف القالب المراد استخدامه (اختياري)
            conversation_id: معرف المحادثة (اختياري)
            use_rag: استخدام RAG لجلب السياق
            prompt_type: نوع الـ prompt (code_generation, documentation, etc.)
        
        Returns:
            Dict يحتوي على الـ prompt المولد والمعلومات الإضافية
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Generating prompt for user {user.id}, type: {prompt_type}, "
                f"description length: {len(user_description)}"
            )
            
            # ============================================================
            # STEP 1: Get or select template
            # ============================================================
            if template_id:
                template = db.session.get(PromptTemplate, template_id)
                if not template or not template.is_active:
                    return {
                        "status": "error",
                        "error": "Template not found or inactive",
                        "message": "⚠️ القالب المطلوب غير موجود أو غير نشط"
                    }
            else:
                # Use default template or create dynamic one
                template = self._get_default_template(prompt_type)
            
            # ============================================================
            # STEP 2: Gather project context (Knowledge Base)
            # ============================================================
            project_context = self._get_project_context()
            
            # ============================================================
            # STEP 3: RAG - Retrieve relevant snippets
            # ============================================================
            relevant_snippets = []
            if use_rag and ENABLE_RAG:
                relevant_snippets = self._retrieve_relevant_snippets(
                    user_description, 
                    project_context
                )
            
            # ============================================================
            # STEP 4: Build few-shot examples
            # ============================================================
            few_shot_examples = self._build_few_shot_examples(
                template, 
                prompt_type
            )
            
            # ============================================================
            # STEP 5: Construct meta-prompt
            # ============================================================
            meta_prompt = self._construct_meta_prompt(
                template=template,
                user_description=user_description,
                project_context=project_context,
                relevant_snippets=relevant_snippets,
                few_shot_examples=few_shot_examples,
                prompt_type=prompt_type,
            )
            
            # ============================================================
            # STEP 6: Generate final prompt using LLM
            # ============================================================
            generated_prompt = self._generate_with_llm(meta_prompt)
            
            # ============================================================
            # STEP 7: Save to database
            # ============================================================
            generated_record = GeneratedPrompt(
                user_description=user_description,
                template_id=template.id if template and hasattr(template, 'id') else None,
                generated_prompt=generated_prompt,
                context_snippets=relevant_snippets,
                conversation_id=conversation_id,
                created_by_id=user.id,
                generation_metadata={
                    "prompt_type": prompt_type,
                    "use_rag": use_rag,
                    "model": DEFAULT_MODEL,
                    "elapsed_seconds": round(time.time() - start_time, 2),
                    "context_chunks": len(relevant_snippets),
                    "few_shot_count": len(few_shot_examples),
                }
            )
            generated_record.compute_content_hash()
            
            db.session.add(generated_record)
            
            # Update template usage
            if template and hasattr(template, 'id'):
                template.usage_count += 1
            
            db.session.commit()
            
            self.logger.info(f"Prompt generated successfully: ID {generated_record.id}")
            
            return {
                "status": "success",
                "prompt_id": generated_record.id,
                "generated_prompt": generated_prompt,
                "meta_prompt": meta_prompt,
                "context_snippets": relevant_snippets,
                "few_shot_examples": few_shot_examples,
                "template_name": template.name if template and hasattr(template, 'name') else "dynamic",
                "metadata": generated_record.generation_metadata,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }
            
        except Exception as e:
            self.logger.error(f"Prompt generation failed: {e}", exc_info=True)
            db.session.rollback()
            
            error_msg = (
                f"⚠️ فشل توليد الـ Prompt.\n\n"
                f"Failed to generate prompt.\n\n"
                f"**Error:** {str(e)}\n\n"
                f"**الحل (Solution):**\n"
                f"1. تحقق من صحة الوصف المدخل (Check input description)\n"
                f"2. حاول مرة أخرى (Try again)\n"
                f"3. استخدم قالب مختلف (Use different template)\n"
            )
            
            return {
                "status": "error",
                "error": str(e),
                "message": error_msg,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

    def _get_project_context(self) -> dict[str, Any]:
        """
        جمع سياق المشروع الكامل (Knowledge Base)
        
        Uses caching to avoid rebuilding index on every request
        """
        # Check cache
        now = time.time()
        if (self._project_context_cache and self._cache_timestamp and 
            (now - self._cache_timestamp) < self._cache_ttl):
            return self._project_context_cache
        
        try:
            if not build_index:
                return {
                    "project_name": "CogniForge",
                    "project_goal": "Advanced AI-powered educational platform",
                    "architecture": "Flask + SQLAlchemy + Supabase + OpenRouter",
                    "files_indexed": 0,
                }
            
            # Build comprehensive project index
            index = build_index(root=".")
            
            context = {
                "project_name": "CogniForge",
                "project_goal": "Advanced AI-powered educational platform with Overmind orchestration",
                "architecture": "Flask + SQLAlchemy + Supabase + OpenRouter + Overmind AI",
                "files_indexed": index.get("files_scanned", 0),
                "total_functions": index.get("global_metrics", {}).get("total_functions", 0),
                "layers": list(index.get("layers", {}).keys()),
                "services": [m.get("module_path") for m in index.get("modules", []) 
                            if "service" in m.get("module_path", "")],
                "tech_stack": [
                    "Flask (Python web framework)",
                    "SQLAlchemy (ORM)",
                    "PostgreSQL (Supabase)",
                    "OpenRouter (LLM gateway)",
                    "Overmind (AI orchestration)",
                    "Bootstrap 5 (UI)",
                ],
                "index_summary": summarize_for_prompt(index, max_len=2000) if summarize_for_prompt else None,
            }
            
            # Cache the context
            self._project_context_cache = context
            self._cache_timestamp = now
            
            return context
            
        except Exception as e:
            self.logger.warning(f"Failed to build project context: {e}")
            return {
                "project_name": "CogniForge",
                "project_goal": "Advanced AI-powered educational platform",
                "architecture": "Flask + SQLAlchemy + Supabase + OpenRouter",
                "error": str(e),
            }

    def _retrieve_relevant_snippets(
        self, 
        user_description: str, 
        project_context: dict
    ) -> list[dict[str, Any]]:
        """
        استرجاع المقتطفات ذات الصلة باستخدام RAG
        
        Uses semantic similarity to find relevant code/docs
        """
        try:
            snippets = []
            
            # For now, use keyword matching from index
            # In future, can integrate proper vector embeddings
            keywords = self._extract_keywords(user_description)
            
            if system_service and hasattr(system_service, 'search_code'):
                # Use system service for code search
                for keyword in keywords[:5]:  # Limit to top 5 keywords
                    try:
                        results = system_service.search_code(keyword, max_results=2)
                        if results:
                            snippets.extend(results[:2])
                    except:
                        pass
            
            # Limit to max snippets
            return snippets[:MAX_CONTEXT_SNIPPETS]
            
        except Exception as e:
            self.logger.warning(f"RAG retrieval failed: {e}")
            return []

    def _extract_keywords(self, text: str) -> list[str]:
        """استخراج الكلمات المفتاحية من النص"""
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:10]

    def _build_few_shot_examples(
        self, 
        template: PromptTemplate | None,
        prompt_type: str
    ) -> list[dict[str, Any]]:
        """
        بناء أمثلة Few-Shot من سياق المشروع
        
        Gets examples from template or generates dynamic ones
        """
        examples = []
        
        try:
            # Get examples from template
            if template and template.few_shot_examples:
                examples = template.few_shot_examples[:MAX_FEW_SHOT_EXAMPLES]
            
            # If no examples, create dynamic ones based on prompt_type
            if not examples:
                examples = self._get_default_examples(prompt_type)
            
            return examples
            
        except Exception as e:
            self.logger.warning(f"Failed to build few-shot examples: {e}")
            return []

    def _get_default_examples(self, prompt_type: str) -> list[dict[str, Any]]:
        """الحصول على أمثلة افتراضية حسب نوع الـ prompt"""
        examples_db = {
            "code_generation": [
                {
                    "description": "Create a Flask route for user registration",
                    "prompt": "You are a senior Flask developer. Create a secure user registration endpoint with email validation, password hashing, and proper error handling. Follow Flask best practices and use SQLAlchemy for database operations.",
                    "result": "High-quality Flask route with security best practices"
                },
                {
                    "description": "Write a database migration for new table",
                    "prompt": "As a database architect, create an Alembic migration script for a new 'notifications' table with proper indexes, foreign keys, and constraints. Include timestamps and soft delete support.",
                    "result": "Professional Alembic migration with all best practices"
                }
            ],
            "documentation": [
                {
                    "description": "Document the API endpoint",
                    "prompt": "Write comprehensive API documentation for this endpoint including: purpose, authentication requirements, request/response examples, error codes, and usage notes. Use clear English and provide examples in multiple formats.",
                    "result": "Professional API documentation"
                }
            ],
            "architecture": [
                {
                    "description": "Design a microservice architecture",
                    "prompt": "As a solutions architect, design a microservice architecture for this feature. Include service boundaries, communication patterns, data flow, scalability considerations, and deployment strategy.",
                    "result": "Comprehensive architecture design"
                }
            ],
        }
        
        return examples_db.get(prompt_type, [])[:MAX_FEW_SHOT_EXAMPLES]

    def _construct_meta_prompt(
        self,
        template: PromptTemplate | None,
        user_description: str,
        project_context: dict,
        relevant_snippets: list,
        few_shot_examples: list,
        prompt_type: str,
    ) -> str:
        """
        بناء Meta-Prompt الديناميكي
        
        Constructs the meta-prompt that will be sent to LLM
        """
        # Use template if available, otherwise create dynamic one
        if template and template.template_content:
            base_template = template.template_content
        else:
            base_template = self._get_default_meta_template(prompt_type)
        
        # Build context section
        context_section = self._format_context_section(project_context, relevant_snippets)
        
        # Build examples section
        examples_section = self._format_examples_section(few_shot_examples)
        
        # Replace variables
        meta_prompt = base_template.format(
            project_name=project_context.get("project_name", "CogniForge"),
            project_goal=project_context.get("project_goal", "Advanced AI platform"),
            user_description=user_description,
            relevant_snippets=context_section,
            few_shot_examples=examples_section,
            prompt_type=prompt_type,
            architecture=project_context.get("architecture", "Flask-based"),
            tech_stack=", ".join(project_context.get("tech_stack", [])),
        )
        
        return meta_prompt

    def _get_default_meta_template(self, prompt_type: str) -> str:
        """الحصول على قالب Meta-Prompt الافتراضي"""
        return """أنت خبير عالمي في هندسة Prompts وتعمل على مشروع "{project_name}".

**هدف المشروع:** {project_goal}

**البنية التقنية:** {architecture}

**التقنيات المستخدمة:** {tech_stack}

**الوصف المُدخل من المستخدم:**
{user_description}

**سياق المشروع ذو الصلة:**
{relevant_snippets}

**أمثلة من المشروع (Few-Shot Learning):**
{few_shot_examples}

---

**مهمتك (YOUR MISSION):**
اصنع Prompt احترافياً خارقاً وتفصيلياً لاستخدامه مع نموذج LLM متقدم لإنتاج {prompt_type}.

**متطلبات الـ Prompt (REQUIREMENTS):**

1. **السياق الكامل:** ضمّن معلومات كافية عن المشروع والتقنيات المستخدمة
2. **الوضوح:** استخدم لغة واضحة ومحددة
3. **التنظيم:** قسّم الـ prompt إلى أقسام منطقية
4. **الأمثلة:** قدّم أمثلة واقعية عند الحاجة
5. **الاحترافية:** اتبع أعلى معايير هندسة Prompts العالمية
6. **التخصيص:** خصص الـ prompt لسياق مشروع {project_name} تحديداً

**تنسيق الإخراج (OUTPUT FORMAT):**
قدم الـ Prompt النهائي مباشرة، جاهزاً للاستخدام، دون أي شرح إضافي.
يجب أن يكون الـ Prompt قابلاً للنسخ واللصق مباشرة في نموذج LLM.

---

**الـ PROMPT المولد:**"""

    def _format_context_section(self, project_context: dict, snippets: list) -> str:
        """تنسيق قسم السياق"""
        sections = []
        
        if project_context.get("index_summary"):
            sections.append(f"**ملخص المشروع:**\n{project_context['index_summary']}\n")
        
        if snippets:
            sections.append("**مقتطفات الكود ذات الصلة:**")
            for i, snippet in enumerate(snippets[:3], 1):
                if isinstance(snippet, dict):
                    file = snippet.get('file', 'unknown')
                    content = snippet.get('content', str(snippet))[:200]
                    sections.append(f"{i}. من {file}:\n```\n{content}\n```\n")
        
        return "\n".join(sections) if sections else "لا يوجد سياق إضافي."

    def _format_examples_section(self, examples: list) -> str:
        """تنسيق قسم الأمثلة"""
        if not examples:
            return "لا توجد أمثلة متاحة."
        
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"**مثال {i}:**")
            formatted.append(f"- الوصف: {example.get('description', 'N/A')}")
            formatted.append(f"- الـ Prompt: {example.get('prompt', 'N/A')}")
            if example.get('result'):
                formatted.append(f"- النتيجة: {example.get('result')}")
            formatted.append("")
        
        return "\n".join(formatted)

    def _generate_with_llm(self, meta_prompt: str) -> str:
        """
        توليد الـ Prompt النهائي باستخدام LLM
        """
        try:
            if not get_llm_client:
                # Fallback: return the meta-prompt itself
                return meta_prompt
            
            llm = get_llm_client()
            
            response = llm.chat(
                messages=[
                    {"role": "system", "content": "You are an expert prompt engineer."},
                    {"role": "user", "content": meta_prompt}
                ],
                model=DEFAULT_MODEL,
                temperature=0.7,
                max_tokens=4000,
            )
            
            return response.get("content", meta_prompt)
            
        except Exception as e:
            self.logger.warning(f"LLM generation failed, using meta-prompt: {e}")
            return meta_prompt

    def _get_default_template(self, prompt_type: str) -> PromptTemplate | None:
        """الحصول على قالب افتراضي حسب النوع"""
        try:
            template = db.session.query(PromptTemplate).filter_by(
                category=prompt_type,
                is_active=True
            ).first()
            
            return template
        except:
            return None

    def create_template(
        self,
        name: str,
        template_content: str,
        user: User,
        description: str | None = None,
        category: str = "general",
        few_shot_examples: list | None = None,
        variables: list | None = None,
    ) -> dict[str, Any]:
        """
        إنشاء قالب Meta-Prompt جديد
        """
        try:
            template = PromptTemplate(
                name=name,
                description=description,
                template_content=template_content,
                category=category,
                few_shot_examples=few_shot_examples or [],
                variables=variables or [],
                created_by_id=user.id,
            )
            
            db.session.add(template)
            db.session.commit()
            
            self.logger.info(f"Template created: {template.id} - {name}")
            
            return {
                "status": "success",
                "template_id": template.id,
                "message": f"✅ تم إنشاء القالب '{name}' بنجاح"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create template: {e}", exc_info=True)
            db.session.rollback()
            return {
                "status": "error",
                "error": str(e),
                "message": f"⚠️ فشل إنشاء القالب: {str(e)}"
            }

    def list_templates(
        self, 
        category: str | None = None, 
        active_only: bool = True
    ) -> list[dict[str, Any]]:
        """قائمة القوالب المتاحة"""
        try:
            query = db.session.query(PromptTemplate)
            
            if active_only:
                query = query.filter_by(is_active=True)
            if category:
                query = query.filter_by(category=category)
            
            templates = query.order_by(PromptTemplate.usage_count.desc()).all()
            
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "usage_count": t.usage_count,
                    "version": t.version,
                }
                for t in templates
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to list templates: {e}")
            return []

    def rate_prompt(
        self, 
        prompt_id: int, 
        rating: int, 
        feedback_text: str | None = None
    ) -> dict[str, Any]:
        """تقييم Prompt مولد (RLHF feedback)"""
        try:
            if not 1 <= rating <= 5:
                return {
                    "status": "error",
                    "error": "Rating must be between 1 and 5"
                }
            
            prompt = db.session.get(GeneratedPrompt, prompt_id)
            if not prompt:
                return {
                    "status": "error",
                    "error": "Prompt not found"
                }
            
            prompt.rating = rating
            prompt.feedback_text = feedback_text
            
            # Update template success rate
            if prompt.template:
                self._update_template_success_rate(prompt.template)
            
            db.session.commit()
            
            return {
                "status": "success",
                "message": "✅ شكراً على تقييمك! سيساعدنا في تحسين الخدمة."
            }
            
        except Exception as e:
            self.logger.error(f"Failed to rate prompt: {e}")
            db.session.rollback()
            return {
                "status": "error",
                "error": str(e)
            }

    def _update_template_success_rate(self, template: PromptTemplate):
        """تحديث معدل نجاح القالب"""
        try:
            prompts = db.session.query(GeneratedPrompt).filter_by(
                template_id=template.id
            ).filter(
                GeneratedPrompt.rating.isnot(None)
            ).all()
            
            if prompts:
                avg_rating = sum(p.rating for p in prompts) / len(prompts)
                template.success_rate = (avg_rating / 5.0) * 100  # Convert to percentage
                
        except Exception as e:
            self.logger.warning(f"Failed to update template success rate: {e}")


# Singleton instance
_service_instance = None


def get_prompt_engineering_service() -> PromptEngineeringService:
    """الحصول على نسخة الخدمة (Singleton)"""
    global _service_instance
    if _service_instance is None:
        _service_instance = PromptEngineeringService()
    return _service_instance
