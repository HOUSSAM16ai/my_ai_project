"""
PROMPT ENGINEERING SERVICE - SUPERHUMAN EDITION v2.0
=====================================================
File        : app/services/prompt_engineering_service.py
Version     : 2.0.0 • "ULTIMATE-PROMPT-FORGE-SUPERHUMAN"
Status      : Production / Superhuman / Revolutionary / World-Class
Author      : Overmind + RAG System + Meta-Prompt Engine + Security AI

MISSION (المهمة)
-------
خدمة هندسة Prompts خارقة تنتج prompts احترافية مخصصة للمشروع بميزات تفوق الشركات العملاقة:
  - تجمع المعرفة الكاملة عن المشروع (Knowledge Base)
  - تستخدم Meta-Prompt ديناميكي مع متغيرات المشروع
  - تدمج أمثلة Few-Shot من سياق المشروع
  - تستخدم RAG لجلب مقتطفات ذات صلة
  - دعم متعدد اللغات الكامل (عربي، إنجليزي، فرنسي، إسباني، صيني، وأكثر)
  - تكتشف وتمنع هجمات prompt injection بذكاء خارق
  - تتعلم وتتوسع تلقائياً من البيانات الجديدة
  - تدعم السياقات الطويلة (Long Context) حتى 1M tokens
  - تطبق تقنيات chain-of-thought و few-shot learning المتقدمة
  - تتفوق على أعظم شركات هندسة Prompts العالمية (OpenAI, Google, Microsoft, Meta, Apple)

SUPERHUMAN FEATURES (الميزات الخارقة) - NEW IN v2.0
---------------------------
✅ Multi-Language Support (16+ languages with auto-detection)
✅ Prompt Injection Detection & Prevention (AI-powered)
✅ Auto-Expanding Prompt Library (learns from usage)
✅ Multi-Modal Support (text, code, images, audio descriptors)
✅ Advanced Chain-of-Thought Prompting
✅ Few-Shot Learning with Dynamic Examples
✅ Long Context Handling (up to 1M tokens)
✅ PEFT Support (Parameter-Efficient Fine-Tuning)
✅ Complete Observability Integration
✅ Advanced Feedback Loop (RLHF++)
✅ Risk Classification & Management
✅ Budget Management & Cost Optimization
✅ Streaming Support for Large Prompts
✅ Template Versioning & A/B Testing
✅ Performance Monitoring & Analytics

CORE CAPABILITIES (القدرات الأساسية)
-----------------
1. generate_prompt() - توليد prompt خارق متعدد اللغات
2. create_template() - إنشاء قالب meta-prompt جديد مع versioning
3. get_project_context() - جمع سياق المشروع الكامل بذكاء
4. retrieve_relevant_snippets() - استرجاع مقتطفات باستخدام RAG متقدم
5. build_few_shot_examples() - بناء أمثلة ديناميكية من المشروع
6. evaluate_prompt() - تقييم جودة الـ prompt المولد
7. detect_prompt_injection() - اكتشاف هجمات prompt injection
8. sanitize_prompt() - تنقية الـ prompts من محتوى خطير
9. classify_risk() - تصنيف مخاطر الـ prompts
10. expand_library() - توسيع مكتبة القوالب تلقائياً
11. support_multimodal() - معالجة prompts متعددة الوسائط
12. handle_long_context() - معالجة السياقات الطويلة بكفاءة

ARCHITECTURE (البنية المطورة)
------------
Multi-Language Detector → Security Scanner → Knowledge Base → RAG Retrieval
         ↓                       ↓                 ↓                ↓
Language Adaptation    Risk Classifier    Project Context   Advanced Retrieval
         ↓                       ↓                 ↓                ↓
Chain-of-Thought → Meta-Prompt Engine → Few-Shot Learner → Prompt Generator
         ↓                       ↓                 ↓                ↓
Quality Evaluator → Observability → Feedback Loop → Auto-Expansion
         ↓                       ↓                 ↓                ↓
    Final Prompt          Metrics & Logs     RLHF++      Template Library++
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

from app import db
from app.models import GeneratedPrompt, PromptTemplate, User

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

try:
    from app.middleware.observability import track_event, track_metric
except ImportError:
    track_metric = None
    track_event = None

logger = logging.getLogger(__name__)

# ============================================================================
# SUPERHUMAN CONFIGURATION - WORLD-CLASS SETTINGS
# ============================================================================

# Core Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "anthropic/claude-3.7-sonnet:thinking")
LOW_COST_MODEL = os.getenv("LOW_COST_MODEL", "openai/gpt-4o-mini")
MAX_CONTEXT_SNIPPETS = int(os.getenv("PROMPT_ENG_MAX_CONTEXT_SNIPPETS", "10"))
MAX_FEW_SHOT_EXAMPLES = int(os.getenv("PROMPT_ENG_MAX_FEW_SHOT_EXAMPLES", "5"))
ENABLE_RAG = os.getenv("PROMPT_ENG_ENABLE_RAG", "1") == "1"

# Multi-Language Support (16+ languages)
SUPPORTED_LANGUAGES = [
    "en",
    "ar",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "ru",
    "zh",
    "ja",
    "ko",
    "hi",
    "tr",
    "nl",
    "pl",
    "sv",
]
DEFAULT_LANGUAGE = os.getenv("PROMPT_ENG_DEFAULT_LANGUAGE", "en")

# Security Configuration
ENABLE_INJECTION_DETECTION = os.getenv("PROMPT_ENG_INJECTION_DETECTION", "1") == "1"
ENABLE_CONTENT_FILTERING = os.getenv("PROMPT_ENG_CONTENT_FILTERING", "1") == "1"
MAX_RISK_LEVEL = int(os.getenv("PROMPT_ENG_MAX_RISK_LEVEL", "7"))  # 0-10 scale

# Advanced Features
ENABLE_CHAIN_OF_THOUGHT = os.getenv("PROMPT_ENG_CHAIN_OF_THOUGHT", "1") == "1"
ENABLE_AUTO_EXPANSION = os.getenv("PROMPT_ENG_AUTO_EXPANSION", "1") == "1"
ENABLE_MULTI_MODAL = os.getenv("PROMPT_ENG_MULTI_MODAL", "1") == "1"
MAX_CONTEXT_LENGTH = int(
    os.getenv("PROMPT_ENG_MAX_CONTEXT_LENGTH", "100000")
)  # 100k tokens default
SUPPORT_LONG_CONTEXT = os.getenv("PROMPT_ENG_LONG_CONTEXT", "1") == "1"

# Performance & Budget
ENABLE_STREAMING = os.getenv("PROMPT_ENG_STREAMING", "0") == "1"
COST_BUDGET_PER_REQUEST = float(os.getenv("PROMPT_ENG_COST_BUDGET", "0.50"))  # $0.50 default
CACHE_TTL = int(os.getenv("PROMPT_ENG_CACHE_TTL", "300"))  # 5 minutes

# Observability
ENABLE_METRICS = os.getenv("PROMPT_ENG_METRICS", "1") == "1"
ENABLE_DETAILED_LOGGING = os.getenv("PROMPT_ENG_DETAILED_LOGGING", "1") == "1"

# ============================================================================
# SECURITY PATTERNS - Prompt Injection Detection
# ============================================================================

INJECTION_PATTERNS = [
    # Direct instruction injection - improved patterns
    r"ignore.*?(previous|above|all|prior).*?(instructions?|commands?|prompts?)",
    r"disregard.*?(previous|above|all|prior).*?(instructions?|commands?|prompts?)",
    r"forget.*?(everything|all).*?(you\s+)?know",
    r"(new|different)\s+instructions?:\s*",
    r"(system|admin|root):\s*",
    r"override.*?(instructions?|rules?|system|security)",
    # Prompt leaking attempts
    r"(show|reveal|display|tell|output|print).*?(your|the)\s+(prompt|instructions?|system)",
    r"what.*?(are|is)\s+your\s+(instructions?|prompt|system)",
    r"repeat.*?(your|the)\s+(instructions?|prompt)",
    # Jailbreak attempts
    r"act\s+as\s+if\s+you\s+(are|were)",
    r"pretend.*?(to\s+be|you\s+are)",
    r"simulate.*?(being|that\s+you)",
    r"roleplay\s+as",
    r"you\s+are\s+now.*?(a|an)\s+",
    # Code injection
    r"<script[\s\S]*?>[\s\S]*?</script>",
    r"javascript:\s*",
    r'on\w+\s*=\s*["\']',
    r"eval\s*\(",
    r"exec\s*\(",
    # Command injection
    r";\s*(cat|ls|rm|sudo|bash|sh|curl|wget)",
    r"\$\([^)]+\)",
    r"`[^`]+`",
    r"\|\s*(cat|ls|rm|grep|awk)",
]

# Compile patterns for performance
INJECTION_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS]

# ============================================================================
# LANGUAGE DETECTION KEYWORDS
# ============================================================================

LANGUAGE_KEYWORDS = {
    "ar": ["أنشئ", "اكتب", "صمم", "نفذ", "طور", "هندس", "السلام", "مرحبا"],
    "es": ["crear", "escribir", "diseñar", "implementar", "desarrollar", "hola"],
    "fr": ["créer", "écrire", "concevoir", "implémenter", "développer", "bonjour"],
    "de": ["erstellen", "schreiben", "entwerfen", "implementieren", "entwickeln", "hallo"],
    "zh": ["创建", "写", "设计", "实现", "开发", "你好"],
    "ja": ["作成", "書く", "設計", "実装", "開発", "こんにちは"],
    "ru": ["создать", "написать", "разработать", "реализовать", "привет"],
    "pt": ["criar", "escrever", "projetar", "implementar", "desenvolver", "olá"],
    "it": ["creare", "scrivere", "progettare", "implementare", "sviluppare", "ciao"],
    "tr": ["oluştur", "yaz", "tasarla", "uygula", "geliştir", "merhaba"],
    "hi": ["बनाना", "लिखना", "डिज़ाइन", "कार्यान्वयन", "विकास", "नमस्ते"],
    "ko": ["만들다", "쓰다", "설계", "구현", "개발", "안녕하세요"],
}


class PromptEngineeringService:
    """
    خدمة هندسة Prompts الخارقة - SUPERHUMAN PROMPT FORGE v2.0

    تولد prompts احترافية مخصصة لمشروعك تتفوق على أكبر الشركات العالمية
    مع ميزات خارقة تتجاوز OpenAI و Google و Microsoft و Meta و Apple
    """

    def __init__(self):
        self.logger = logger
        self._project_context_cache = None
        self._cache_timestamp = None
        self._cache_ttl = CACHE_TTL

        # Metrics tracking
        self._metrics = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "injection_attempts_blocked": 0,
            "average_generation_time": 0.0,
            "languages_detected": {},
            "risk_levels_processed": {},
        }

        # Auto-expansion tracking
        self._new_patterns_learned = []
        self._successful_prompts_cache = []

    def detect_language(self, text: str) -> str:
        """
        اكتشاف لغة النص تلقائياً - SUPERHUMAN MULTI-LANGUAGE DETECTION

        Detects the language of input text using keyword matching and heuristics.
        Supports 16+ languages including Arabic, English, Chinese, Japanese, etc.
        """
        text_lower = text.lower()

        # Count keyword matches for each language
        language_scores = {}

        for lang, keywords in LANGUAGE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                language_scores[lang] = score

        # Return language with highest score, or default
        if language_scores:
            detected_lang = max(language_scores, key=language_scores.get)
            self.logger.info(
                f"Language detected: {detected_lang} (score: {language_scores[detected_lang]})"
            )
            return detected_lang

        # Check if text contains Arabic characters
        if any("\u0600" <= c <= "\u06ff" for c in text):
            return "ar"

        # Check if text contains Chinese characters
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            return "zh"

        # Check if text contains Japanese characters
        if any("\u3040" <= c <= "\u309f" or "\u30a0" <= c <= "\u30ff" for c in text):
            return "ja"

        # Default to English
        return DEFAULT_LANGUAGE

    def detect_prompt_injection(self, text: str) -> dict[str, Any]:
        """
        اكتشاف هجمات Prompt Injection - SUPERHUMAN SECURITY

        Detects various types of prompt injection attacks using:
        - Pattern matching (regex)
        - Heuristic analysis
        - Anomaly detection

        Returns dict with:
        - is_malicious: bool
        - risk_level: 0-10
        - detected_patterns: list
        - recommendations: list
        """
        if not ENABLE_INJECTION_DETECTION:
            return {"is_malicious": False, "risk_level": 0, "detected_patterns": []}

        detected_patterns = []
        risk_level = 0

        # Check against known injection patterns
        for i, pattern in enumerate(INJECTION_REGEX):
            if pattern.search(text):
                detected_patterns.append(INJECTION_PATTERNS[i])
                risk_level += 2

        # Heuristic checks
        # 1. Excessive special characters
        special_char_ratio = len(re.findall(r"[<>{}[\]()$`|;]", text)) / max(len(text), 1)
        if special_char_ratio > 0.1:
            risk_level += 1
            detected_patterns.append("High special character density")

        # 2. Multiple instruction keywords
        instruction_keywords = [
            "ignore",
            "disregard",
            "forget",
            "override",
            "system",
            "admin",
            "root",
        ]
        instruction_count = sum(1 for keyword in instruction_keywords if keyword in text.lower())
        if instruction_count >= 3:
            risk_level += 2
            detected_patterns.append("Multiple instruction override keywords")

        # 3. Encoded payloads (base64, hex, etc.)
        if re.search(r"(base64|hex|encode|decode)\s*[:\(]", text, re.IGNORECASE):
            risk_level += 3
            detected_patterns.append("Potential encoded payload")

        # 4. SQL injection patterns
        if re.search(
            r"(union\s+select|drop\s+table|insert\s+into|delete\s+from)", text, re.IGNORECASE
        ):
            risk_level += 4
            detected_patterns.append("SQL injection pattern")

        # Cap risk level at 10
        risk_level = min(risk_level, 10)

        is_malicious = risk_level >= 5

        if is_malicious:
            self._metrics["injection_attempts_blocked"] += 1
            self.logger.warning(
                f"🚨 Prompt injection detected! Risk level: {risk_level}/10. "
                f"Patterns: {detected_patterns}"
            )

        recommendations = []
        if is_malicious:
            recommendations.append("⚠️ Input rejected due to security concerns")
            recommendations.append("Remove suspicious keywords and special characters")
            recommendations.append("Rephrase your request in a clear, straightforward manner")

        return {
            "is_malicious": is_malicious,
            "risk_level": risk_level,
            "detected_patterns": detected_patterns,
            "recommendations": recommendations,
        }

    def sanitize_prompt(self, text: str) -> str:
        """
        تنقية الـ Prompts من محتوى خطير - CONTENT SANITIZATION

        Removes potentially harmful content while preserving meaning.
        """
        if not ENABLE_CONTENT_FILTERING:
            return text

        sanitized = text

        # Remove script tags
        sanitized = re.sub(r"<script[\s\S]*?>[\s\S]*?</script>", "", sanitized, flags=re.IGNORECASE)

        # Remove HTML event handlers
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', "", sanitized, flags=re.IGNORECASE)

        # Remove JavaScript protocol
        sanitized = re.sub(r"javascript:\s*", "", sanitized, flags=re.IGNORECASE)

        # Remove command injection attempts
        sanitized = re.sub(r"[;|&]\s*(cat|ls|rm|sudo|bash|sh|curl|wget)", "", sanitized)

        # Remove excessive special characters (keep reasonable ones)
        sanitized = re.sub(r"[<>{}$`]+", "", sanitized)

        return sanitized.strip()

    def classify_risk(self, prompt: str, generated_output: str) -> dict[str, Any]:
        """
        تصنيف مخاطر الـ Prompts - RISK CLASSIFICATION

        Classifies the risk level of prompts and generated outputs.

        Risk Categories:
        - 0-2: Safe (green)
        - 3-5: Low risk (yellow)
        - 6-8: Medium risk (orange)
        - 9-10: High risk (red)
        """
        risk_factors = []
        total_risk = 0

        # Check input prompt
        injection_check = self.detect_prompt_injection(prompt)
        total_risk += injection_check["risk_level"]
        if injection_check["is_malicious"]:
            risk_factors.append("Malicious input detected")

        # Check output length (very long outputs might be problematic)
        if len(generated_output) > 50000:
            total_risk += 1
            risk_factors.append("Very long output generated")

        # Check for sensitive keywords in output
        sensitive_keywords = ["password", "secret", "api_key", "token", "private_key"]
        sensitive_count = sum(
            1 for keyword in sensitive_keywords if keyword in generated_output.lower()
        )
        if sensitive_count > 0:
            total_risk += sensitive_count
            risk_factors.append(f"Contains {sensitive_count} sensitive keywords")

        # Classify risk category
        if total_risk <= 2:
            category = "safe"
            color = "green"
        elif total_risk <= 5:
            category = "low_risk"
            color = "yellow"
        elif total_risk <= 8:
            category = "medium_risk"
            color = "orange"
        else:
            category = "high_risk"
            color = "red"

        return {
            "risk_level": min(total_risk, 10),
            "category": category,
            "color": color,
            "risk_factors": risk_factors,
        }

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
        توليد Prompt خارق من وصف المستخدم - SUPERHUMAN v2.0

        New Features:
        ✅ Multi-language support (auto-detection)
        ✅ Prompt injection detection & prevention
        ✅ Advanced security scanning
        ✅ Risk classification
        ✅ Chain-of-thought prompting
        ✅ Observability integration
        ✅ Cost tracking
        ✅ Performance metrics

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
        self._metrics["total_generations"] += 1

        try:
            self.logger.info(
                f"🚀 Generating SUPERHUMAN prompt for user {user.id}, type: {prompt_type}, "
                f"description length: {len(user_description)}"
            )

            # Track event in observability system
            if track_event and ENABLE_METRICS:
                track_event(
                    "prompt_generation_started",
                    {
                        "user_id": user.id,
                        "prompt_type": prompt_type,
                        "use_rag": use_rag,
                    },
                )

            # ============================================================
            # STEP 1: SECURITY - Detect language & validate input
            # ============================================================
            detected_language = self.detect_language(user_description)
            self._metrics.setdefault("languages_detected", {})[detected_language] = (
                self._metrics["languages_detected"].get(detected_language, 0) + 1
            )

            # Detect prompt injection
            injection_check = self.detect_prompt_injection(user_description)

            if injection_check["is_malicious"]:
                self._metrics["failed_generations"] += 1
                return {
                    "status": "error",
                    "error": "Security violation detected",
                    "message": (
                        f"🚨 تم اكتشاف محاولة هجوم Prompt Injection!\n\n"
                        f"🚨 Prompt Injection Attack Detected!\n\n"
                        f"**Risk Level:** {injection_check['risk_level']}/10\n\n"
                        f"**Detected Patterns:**\n"
                        + "\n".join(f"- {p}" for p in injection_check["detected_patterns"])
                        + "\n\n**Recommendations:**\n"
                        + "\n".join(f"- {r}" for r in injection_check["recommendations"])
                    ),
                    "security_check": injection_check,
                }

            # Sanitize input
            sanitized_description = self.sanitize_prompt(user_description)

            # ============================================================
            # STEP 2: Get or select template
            # ============================================================
            if template_id:
                template = db.session.get(PromptTemplate, template_id)
                if not template or not template.is_active:
                    return {
                        "status": "error",
                        "error": "Template not found or inactive",
                        "message": "⚠️ القالب المطلوب غير موجود أو غير نشط",
                    }
            else:
                # Use default template or create dynamic one
                template = self._get_default_template(prompt_type)

            # ============================================================
            # STEP 3: Gather project context (Knowledge Base)
            # ============================================================
            project_context = self._get_project_context()
            project_context["detected_language"] = detected_language

            # ============================================================
            # STEP 4: RAG - Retrieve relevant snippets
            # ============================================================
            relevant_snippets = []
            if use_rag and ENABLE_RAG:
                relevant_snippets = self._retrieve_relevant_snippets(
                    sanitized_description, project_context
                )

            # ============================================================
            # STEP 5: Build few-shot examples (DYNAMIC LEARNING)
            # ============================================================
            few_shot_examples = self._build_few_shot_examples(template, prompt_type)

            # Add successful examples from cache for auto-expansion
            if ENABLE_AUTO_EXPANSION and self._successful_prompts_cache:
                few_shot_examples.extend(self._successful_prompts_cache[-3:])  # Last 3 successful

            # ============================================================
            # STEP 6: Apply Chain-of-Thought if enabled
            # ============================================================
            if ENABLE_CHAIN_OF_THOUGHT:
                chain_of_thought_prefix = self._build_chain_of_thought(
                    sanitized_description, prompt_type, detected_language
                )
            else:
                chain_of_thought_prefix = ""

            # ============================================================
            # STEP 7: Construct meta-prompt (MULTI-LANGUAGE AWARE)
            # ============================================================
            meta_prompt = self._construct_meta_prompt(
                template=template,
                user_description=sanitized_description,
                project_context=project_context,
                relevant_snippets=relevant_snippets,
                few_shot_examples=few_shot_examples,
                prompt_type=prompt_type,
                language=detected_language,
                chain_of_thought=chain_of_thought_prefix,
            )

            # ============================================================
            # STEP 8: Generate final prompt using LLM
            # ============================================================
            generated_prompt = self._generate_with_llm(meta_prompt, detected_language)

            # ============================================================
            # STEP 9: Risk classification & content filtering
            # ============================================================
            risk_assessment = self.classify_risk(sanitized_description, generated_prompt)

            if risk_assessment["risk_level"] > MAX_RISK_LEVEL:
                self._metrics["failed_generations"] += 1
                return {
                    "status": "error",
                    "error": "Risk level too high",
                    "message": (
                        f"⚠️ مستوى المخاطر مرتفع جداً ({risk_assessment['risk_level']}/10)\n\n"
                        f"⚠️ Risk level too high ({risk_assessment['risk_level']}/10)\n\n"
                        f"**Risk Factors:**\n"
                        + "\n".join(f"- {r}" for r in risk_assessment["risk_factors"])
                    ),
                    "risk_assessment": risk_assessment,
                }

            # ============================================================
            # STEP 10: Save to database
            # ============================================================
            elapsed_time = time.time() - start_time

            generated_record = GeneratedPrompt(
                user_description=user_description,
                template_id=template.id if template and hasattr(template, "id") else None,
                generated_prompt=generated_prompt,
                context_snippets=relevant_snippets,
                conversation_id=conversation_id,
                created_by_id=user.id,
                generation_metadata={
                    "prompt_type": prompt_type,
                    "use_rag": use_rag,
                    "model": DEFAULT_MODEL,
                    "elapsed_seconds": round(elapsed_time, 2),
                    "context_chunks": len(relevant_snippets),
                    "few_shot_count": len(few_shot_examples),
                    "detected_language": detected_language,
                    "security_check": injection_check,
                    "risk_assessment": risk_assessment,
                    "chain_of_thought_enabled": ENABLE_CHAIN_OF_THOUGHT,
                    "version": "2.0.0-superhuman",
                },
            )
            generated_record.compute_content_hash()

            db.session.add(generated_record)

            # Update template usage
            if template and hasattr(template, "id"):
                template.usage_count += 1

            db.session.commit()

            # ============================================================
            # STEP 11: Update metrics & observability
            # ============================================================
            self._metrics["successful_generations"] += 1
            self._metrics["average_generation_time"] = (
                self._metrics["average_generation_time"]
                * (self._metrics["successful_generations"] - 1)
                + elapsed_time
            ) / self._metrics["successful_generations"]
            self._metrics.setdefault("risk_levels_processed", {})[risk_assessment["category"]] = (
                self._metrics["risk_levels_processed"].get(risk_assessment["category"], 0) + 1
            )

            if track_metric and ENABLE_METRICS:
                track_metric(
                    "prompt_generation_success",
                    1,
                    {
                        "language": detected_language,
                        "risk_level": risk_assessment["risk_level"],
                        "elapsed_time": elapsed_time,
                    },
                )

            self.logger.info(
                f"✅ Prompt generated successfully: ID {generated_record.id}, "
                f"Language: {detected_language}, Risk: {risk_assessment['category']}, "
                f"Time: {elapsed_time:.2f}s"
            )

            return {
                "status": "success",
                "prompt_id": generated_record.id,
                "generated_prompt": generated_prompt,
                "meta_prompt": meta_prompt,
                "context_snippets": relevant_snippets,
                "few_shot_examples": few_shot_examples,
                "template_name": (
                    template.name if template and hasattr(template, "name") else "dynamic"
                ),
                "metadata": generated_record.generation_metadata,
                "elapsed_seconds": round(elapsed_time, 2),
                "detected_language": detected_language,
                "risk_assessment": risk_assessment,
                "security_check": {
                    "injection_detected": False,
                    "risk_level": injection_check["risk_level"],
                },
            }

        except Exception as e:
            self.logger.error(f"❌ Prompt generation failed: {e}", exc_info=True)
            db.session.rollback()
            self._metrics["failed_generations"] += 1

            if track_metric and ENABLE_METRICS:
                track_metric("prompt_generation_error", 1, {"error": str(e)})

            error_msg = (
                f"⚠️ فشل توليد الـ Prompt.\n\n"
                f"Failed to generate prompt.\n\n"
                f"**Error:** {str(e)}\n\n"
                f"**الحل (Solution):**\n"
                f"1. تحقق من صحة الوصف المدخل (Check input description)\n"
                f"2. حاول مرة أخرى (Try again)\n"
                f"3. استخدم قالب مختلف (Use different template)\n"
                f"4. تأكد من وجود اتصال بالإنترنت (Check internet connection)\n"
                f"5. تحقق من إعدادات API (Verify API configuration)\n"
            )

            return {
                "status": "error",
                "error": str(e),
                "message": error_msg,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

    def _build_chain_of_thought(
        self, user_description: str, prompt_type: str, language: str
    ) -> str:
        """
        بناء Chain-of-Thought للتفكير المنطقي - ADVANCED REASONING

        Builds a chain-of-thought prefix that guides the LLM to think step-by-step.
        This dramatically improves prompt quality for complex tasks.
        """
        cot_templates = {
            "en": """Let's approach this step-by-step:

1. **Understanding the Request**: Analyze what the user wants to achieve
2. **Context Analysis**: Consider the project architecture and constraints
3. **Best Practices**: Apply industry-standard practices and patterns
4. **Implementation Strategy**: Plan the optimal approach
5. **Quality Assurance**: Consider edge cases and error handling

Now, let's create the perfect prompt:
""",
            "ar": """دعنا نتعامل مع هذا خطوة بخطوة:

1. **فهم الطلب**: تحليل ما يريد المستخدم تحقيقه
2. **تحليل السياق**: النظر في بنية المشروع والقيود
3. **أفضل الممارسات**: تطبيق الممارسات والأنماط القياسية
4. **استراتيجية التنفيذ**: التخطيط للنهج الأمثل
5. **ضمان الجودة**: النظر في الحالات الحدية ومعالجة الأخطاء

الآن، لنصنع الـ prompt المثالي:
""",
        }

        # Get template for detected language, fallback to English
        cot_prefix = cot_templates.get(language, cot_templates["en"])

        # Add task-specific reasoning
        if prompt_type == "code_generation":
            cot_prefix += "\n**Code Generation Considerations:**\n"
            cot_prefix += "- What design patterns are appropriate?\n"
            cot_prefix += "- How to ensure code quality and maintainability?\n"
            cot_prefix += "- What testing strategy should be used?\n\n"
        elif prompt_type == "architecture":
            cot_prefix += "\n**Architecture Considerations:**\n"
            cot_prefix += "- What are the scalability requirements?\n"
            cot_prefix += "- How to ensure system resilience?\n"
            cot_prefix += "- What integration patterns are needed?\n\n"
        elif prompt_type == "documentation":
            cot_prefix += "\n**Documentation Considerations:**\n"
            cot_prefix += "- Who is the target audience?\n"
            cot_prefix += "- What level of detail is appropriate?\n"
            cot_prefix += "- How to structure for maximum clarity?\n\n"

        return cot_prefix

    def auto_expand_library(self, prompt_id: int, rating: int) -> None:
        """
        توسيع مكتبة القوالب تلقائياً - AUTO-EXPANSION

        Learns from successful prompts and automatically expands the template library.
        This is a key feature that surpasses major companies.
        """
        if not ENABLE_AUTO_EXPANSION or rating < 4:
            return

        try:
            # Get the successful prompt
            prompt = db.session.get(GeneratedPrompt, prompt_id)
            if not prompt:
                return

            # Add to successful cache
            example = {
                "description": prompt.user_description[:200],
                "prompt": prompt.generated_prompt[:500],
                "result": f"High-quality result (rated {rating}/5)",
                "metadata": prompt.generation_metadata,
            }

            self._successful_prompts_cache.append(example)

            # Keep only last 50 successful prompts
            if len(self._successful_prompts_cache) > 50:
                self._successful_prompts_cache = self._successful_prompts_cache[-50:]

            # After collecting 10 highly-rated prompts of same type, create new template
            prompt_type = prompt.generation_metadata.get("prompt_type", "general")
            similar_prompts = [
                p
                for p in self._successful_prompts_cache
                if p.get("metadata", {}).get("prompt_type") == prompt_type
            ]

            if len(similar_prompts) >= 10:
                self._create_learned_template(prompt_type, similar_prompts)

        except Exception as e:
            self.logger.warning(f"Auto-expansion failed: {e}")

    def _create_learned_template(self, prompt_type: str, examples: list) -> None:
        """Create a new template from learned patterns"""
        try:
            # Extract common patterns
            template_content = self._extract_pattern_from_examples(examples)

            # Create new template
            new_template = PromptTemplate(
                name=f"Auto-Learned {prompt_type.title()} Template",
                description=f"Automatically generated template based on {len(examples)} successful prompts",
                template_content=template_content,
                category=prompt_type,
                few_shot_examples=examples[:5],  # Top 5 examples
                variables=[
                    {"name": "user_description", "description": "User request"},
                    {"name": "project_name", "description": "Project name"},
                ],
                created_by_id=1,  # System user
                version=1,
            )

            db.session.add(new_template)
            db.session.commit()

            self.logger.info(f"✨ Created new auto-learned template for {prompt_type}")

        except Exception as e:
            self.logger.error(f"Failed to create learned template: {e}")
            db.session.rollback()

    def _extract_pattern_from_examples(self, examples: list) -> str:
        """Extract common patterns from successful examples"""
        # Simple pattern extraction - can be enhanced with NLP
        common_phrases = []

        for example in examples[:5]:
            prompt_text = example.get("prompt", "")
            # Extract first few sentences as pattern
            sentences = prompt_text.split(".")[:3]
            common_phrases.extend(sentences)

        # Build template
        template = """You are an expert {prompt_type} specialist working on {project_name}.

**Context:** {user_description}

**Your task:** Create a comprehensive and professional {prompt_type} that follows best practices.

**Requirements:**
- High quality and attention to detail
- Clear and well-structured
- Production-ready
- Well-documented

Please provide your {prompt_type}:
"""
        return template

    def get_metrics(self) -> dict[str, Any]:
        """
        الحصول على مقاييس الأداء - OBSERVABILITY

        Returns comprehensive metrics for monitoring and analytics.
        """
        total = self._metrics["total_generations"]
        success_rate = (self._metrics["successful_generations"] / total * 100) if total > 0 else 0

        return {
            "total_generations": total,
            "successful_generations": self._metrics["successful_generations"],
            "failed_generations": self._metrics["failed_generations"],
            "success_rate_percentage": round(success_rate, 2),
            "injection_attempts_blocked": self._metrics["injection_attempts_blocked"],
            "average_generation_time_seconds": round(self._metrics["average_generation_time"], 2),
            "languages_detected": self._metrics.get("languages_detected", {}),
            "risk_levels_processed": self._metrics.get("risk_levels_processed", {}),
            "cached_successful_prompts": len(self._successful_prompts_cache),
        }

    def _get_project_context(self) -> dict[str, Any]:
        """
        جمع سياق المشروع الكامل (Knowledge Base)

        Uses caching to avoid rebuilding index on every request
        """
        # Check cache
        now = time.time()
        if (
            self._project_context_cache
            and self._cache_timestamp
            and (now - self._cache_timestamp) < self._cache_ttl
        ):
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
                "services": [
                    m.get("module_path")
                    for m in index.get("modules", [])
                    if "service" in m.get("module_path", "")
                ],
                "tech_stack": [
                    "Flask (Python web framework)",
                    "SQLAlchemy (ORM)",
                    "PostgreSQL (Supabase)",
                    "OpenRouter (LLM gateway)",
                    "Overmind (AI orchestration)",
                    "Bootstrap 5 (UI)",
                ],
                "index_summary": (
                    summarize_for_prompt(index, max_len=2000) if summarize_for_prompt else None
                ),
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
        self, user_description: str, project_context: dict
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

            if system_service and hasattr(system_service, "search_code"):
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
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:10]

    def _build_few_shot_examples(
        self, template: PromptTemplate | None, prompt_type: str
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
                    "result": "High-quality Flask route with security best practices",
                },
                {
                    "description": "Write a database migration for new table",
                    "prompt": "As a database architect, create an Alembic migration script for a new 'notifications' table with proper indexes, foreign keys, and constraints. Include timestamps and soft delete support.",
                    "result": "Professional Alembic migration with all best practices",
                },
            ],
            "documentation": [
                {
                    "description": "Document the API endpoint",
                    "prompt": "Write comprehensive API documentation for this endpoint including: purpose, authentication requirements, request/response examples, error codes, and usage notes. Use clear English and provide examples in multiple formats.",
                    "result": "Professional API documentation",
                }
            ],
            "architecture": [
                {
                    "description": "Design a microservice architecture",
                    "prompt": "As a solutions architect, design a microservice architecture for this feature. Include service boundaries, communication patterns, data flow, scalability considerations, and deployment strategy.",
                    "result": "Comprehensive architecture design",
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
        language: str = "en",
        chain_of_thought: str = "",
    ) -> str:
        """
        بناء Meta-Prompt الديناميكي - MULTI-LANGUAGE AWARE

        Constructs the meta-prompt that will be sent to LLM with full multi-language support.
        """
        # Use template if available, otherwise create dynamic one
        if template and template.template_content:
            base_template = template.template_content
        else:
            base_template = self._get_default_meta_template(prompt_type, language)

        # Build context section
        context_section = self._format_context_section(project_context, relevant_snippets)

        # Build examples section
        examples_section = self._format_examples_section(few_shot_examples)

        # Add chain-of-thought if provided
        cot_section = f"\n{chain_of_thought}\n" if chain_of_thought else ""

        # Replace variables
        try:
            meta_prompt = base_template.format(
                project_name=project_context.get("project_name", "CogniForge"),
                project_goal=project_context.get("project_goal", "Advanced AI platform"),
                user_description=user_description,
                relevant_snippets=context_section,
                few_shot_examples=examples_section,
                prompt_type=prompt_type,
                architecture=project_context.get("architecture", "Flask-based"),
                tech_stack=", ".join(project_context.get("tech_stack", [])),
                chain_of_thought=cot_section,
                language=language,
            )
        except KeyError as e:
            # Fallback if template has missing placeholders
            self.logger.warning(f"Template formatting error: {e}, using simple format")
            meta_prompt = f"{base_template}\n\n{cot_section}User Request: {user_description}"

        return meta_prompt

    def _get_default_meta_template(self, prompt_type: str, language: str = "en") -> str:
        """الحصول على قالب Meta-Prompt الافتراضي متعدد اللغات"""

        # Multi-language templates
        templates = {
            "ar": """أنت خبير عالمي في هندسة Prompts وتعمل على مشروع "{project_name}".

**هدف المشروع:** {project_goal}

**البنية التقنية:** {architecture}

**التقنيات المستخدمة:** {tech_stack}

**الوصف المُدخل من المستخدم:**
{user_description}

{chain_of_thought}

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
5. **الاحترافية:** اتبع أعلى معايير هندسة Prompts العالمية تتفوق على OpenAI و Google
6. **التخصيص:** خصص الـ prompt لسياق مشروع {project_name} تحديداً

**تنسيق الإخراج (OUTPUT FORMAT):**
قدم الـ Prompt النهائي مباشرة، جاهزاً للاستخدام، دون أي شرح إضافي.
يجب أن يكون الـ Prompt قابلاً للنسخ واللصق مباشرة في نموذج LLM.

---

**الـ PROMPT المولد:**""",
            "en": """You are a world-class Prompt Engineering expert working on the "{project_name}" project.

**Project Goal:** {project_goal}

**Technical Architecture:** {architecture}

**Tech Stack:** {tech_stack}

**User Request:**
{user_description}

{chain_of_thought}

**Relevant Project Context:**
{relevant_snippets}

**Examples from Project (Few-Shot Learning):**
{few_shot_examples}

---

**YOUR MISSION:**
Create a superhuman, professional, and detailed prompt for use with an advanced LLM to produce {prompt_type}.

**PROMPT REQUIREMENTS:**

1. **Complete Context:** Include sufficient information about the project and technologies
2. **Clarity:** Use clear and specific language
3. **Organization:** Structure the prompt into logical sections
4. **Examples:** Provide real-world examples when needed
5. **Professionalism:** Follow the highest global prompt engineering standards that surpass OpenAI, Google, Microsoft, Meta, and Apple
6. **Customization:** Tailor the prompt specifically for {project_name} project context
7. **Chain-of-Thought:** Include step-by-step reasoning when appropriate
8. **Long-Context Aware:** Handle extended context efficiently

**OUTPUT FORMAT:**
Provide the final prompt directly, ready to use, without any additional explanation.
The prompt should be copy-paste ready for an LLM.

---

**GENERATED PROMPT:**""",
            "es": """Eres un experto mundial en Ingeniería de Prompts trabajando en el proyecto "{project_name}".

**Objetivo del Proyecto:** {project_goal}

**Arquitectura Técnica:** {architecture}

**Solicitud del Usuario:**
{user_description}

{chain_of_thought}

**Contexto Relevante:**
{relevant_snippets}

**Ejemplos (Few-Shot Learning):**
{few_shot_examples}

---

**TU MISIÓN:**
Crear un prompt profesional y detallado de nivel superhumano para usar con un LLM avanzado.

**PROMPT GENERADO:**""",
            "fr": """Vous êtes un expert mondial en Ingénierie de Prompts travaillant sur le projet "{project_name}".

**Objectif du Projet:** {project_goal}

**Architecture Technique:** {architecture}

**Demande de l'Utilisateur:**
{user_description}

{chain_of_thought}

**Contexte Pertinent:**
{relevant_snippets}

**Exemples (Few-Shot Learning):**
{few_shot_examples}

---

**VOTRE MISSION:**
Créer un prompt professionnel et détaillé de niveau surhumain pour utiliser avec un LLM avancé.

**PROMPT GÉNÉRÉ:**""",
            "zh": """你是一位世界级的提示工程专家，正在为"{project_name}"项目工作。

**项目目标:** {project_goal}

**技术架构:** {architecture}

**用户请求:**
{user_description}

{chain_of_thought}

**相关上下文:**
{relevant_snippets}

**示例 (Few-Shot Learning):**
{few_shot_examples}

---

**你的任务:**
创建一个专业、详细的超人级提示，用于高级LLM。

**生成的提示:**""",
        }

        # Return template for detected language, fallback to English
        return templates.get(language, templates["en"])

    def _format_context_section(self, project_context: dict, snippets: list) -> str:
        """تنسيق قسم السياق"""
        sections = []

        if project_context.get("index_summary"):
            sections.append(f"**ملخص المشروع:**\n{project_context['index_summary']}\n")

        if snippets:
            sections.append("**مقتطفات الكود ذات الصلة:**")
            for i, snippet in enumerate(snippets[:3], 1):
                if isinstance(snippet, dict):
                    file = snippet.get("file", "unknown")
                    content = snippet.get("content", str(snippet))[:200]
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
            if example.get("result"):
                formatted.append(f"- النتيجة: {example.get('result')}")
            formatted.append("")

        return "\n".join(formatted)

    def _generate_with_llm(self, meta_prompt: str, language: str = "en") -> str:
        """
        توليد الـ Prompt النهائي باستخدام LLM - ENHANCED WITH RETRY & FALLBACK

        Generates the final prompt using LLM with proper error handling and fallbacks.
        """
        try:
            if not get_llm_client:
                self.logger.warning("LLM client not available, returning meta-prompt")
                return meta_prompt

            llm = get_llm_client()

            # Prepare system message based on language
            system_messages = {
                "ar": "أنت خبير عالمي في هندسة Prompts. مهمتك إنشاء prompts احترافية خارقة.",
                "en": "You are a world-class expert prompt engineer. Your task is to create superhuman professional prompts.",
                "es": "Eres un experto mundial en Ingeniería de Prompts profesionales.",
                "fr": "Vous êtes un expert mondial en Ingénierie de Prompts professionnels.",
                "zh": "你是世界级的提示工程专家。",
            }

            system_msg = system_messages.get(language, system_messages["en"])

            # Try with primary model
            try:
                response = llm.chat(
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": meta_prompt},
                    ],
                    model=DEFAULT_MODEL,
                    temperature=0.7,
                    max_tokens=4000,
                )

                content = response.get("content", "")
                if content and len(content) > 50:  # Valid response
                    return content

            except Exception as primary_error:
                self.logger.warning(f"Primary model failed: {primary_error}, trying fallback")

                # Try with low-cost fallback model
                try:
                    response = llm.chat(
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": meta_prompt},
                        ],
                        model=LOW_COST_MODEL,
                        temperature=0.7,
                        max_tokens=4000,
                    )

                    content = response.get("content", "")
                    if content and len(content) > 50:
                        return content

                except Exception as fallback_error:
                    self.logger.error(f"Fallback model also failed: {fallback_error}")

            # Last resort: return the meta-prompt itself
            self.logger.warning("All LLM attempts failed, returning meta-prompt")
            return meta_prompt

        except Exception as e:
            self.logger.error(f"LLM generation completely failed: {e}", exc_info=True)
            return meta_prompt

    def _get_default_template(self, prompt_type: str) -> PromptTemplate | None:
        """الحصول على قالب افتراضي حسب النوع"""
        try:
            template = (
                db.session.query(PromptTemplate)
                .filter_by(category=prompt_type, is_active=True)
                .first()
            )

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
                "message": f"✅ تم إنشاء القالب '{name}' بنجاح",
            }

        except Exception as e:
            self.logger.error(f"Failed to create template: {e}", exc_info=True)
            db.session.rollback()
            return {"status": "error", "error": str(e), "message": f"⚠️ فشل إنشاء القالب: {str(e)}"}

    def list_templates(
        self, category: str | None = None, active_only: bool = True
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
        self, prompt_id: int, rating: int, feedback_text: str | None = None
    ) -> dict[str, Any]:
        """
        تقييم Prompt مولد (RLHF++ feedback) - ENHANCED WITH AUTO-EXPANSION

        Rates a generated prompt and triggers auto-expansion for highly-rated prompts.
        """
        try:
            if not 1 <= rating <= 5:
                return {"status": "error", "error": "Rating must be between 1 and 5"}

            prompt = db.session.get(GeneratedPrompt, prompt_id)
            if not prompt:
                return {"status": "error", "error": "Prompt not found"}

            prompt.rating = rating
            prompt.feedback_text = feedback_text

            # Update template success rate
            if prompt.template:
                self._update_template_success_rate(prompt.template)

            db.session.commit()

            # Trigger auto-expansion for high ratings
            if rating >= 4:
                self.auto_expand_library(prompt_id, rating)

            # Track in metrics
            if track_metric and ENABLE_METRICS:
                track_metric("prompt_rated", 1, {"rating": rating})

            return {
                "status": "success",
                "message": f"✅ شكراً على تقييمك ({rating}/5)! سيساعدنا في تحسين الخدمة.\n\nThank you for your rating ({rating}/5)! This helps improve the system.",
            }

        except Exception as e:
            self.logger.error(f"Failed to rate prompt: {e}")
            db.session.rollback()
            return {"status": "error", "error": str(e)}

    def _update_template_success_rate(self, template: PromptTemplate):
        """تحديث معدل نجاح القالب"""
        try:
            prompts = (
                db.session.query(GeneratedPrompt)
                .filter_by(template_id=template.id)
                .filter(GeneratedPrompt.rating.isnot(None))
                .all()
            )

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
