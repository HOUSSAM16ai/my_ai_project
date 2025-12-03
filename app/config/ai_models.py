# app/config/ai_models.py
"""
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                          ║
║   ██████╗ ██████╗  ██████╗ ███╗   ██╗██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗      ║
║  ██╔════╝██╔═══██╗██╔════╝ ████╗  ██║██║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝      ║
║  ██║     ██║   ██║██║  ███╗██╔██╗ ██║██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗        ║
║  ██║     ██║   ██║██║   ██║██║╚██╗██║██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝        ║
║  ╚██████╗╚██████╔╝╚██████╔╝██║ ╚████║██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗      ║
║   ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ║
║                                                                                          ║
║              🧠 AI MODELS CONFIGURATION CENTER v2.0 - SUPERHUMAN EDITION                ║
║              ════════════════════════════════════════════════════════════                ║
║                                                                                          ║
║   ╔════════════════════════════════════════════════════════════════════════════════╗    ║
║   ║  📍 THIS IS THE ONLY FILE YOU NEED TO EDIT TO CHANGE AI MODELS                ║    ║
║   ║  📍 هذا هو الملف الوحيد الذي تحتاج تعديله لتغيير نماذج الذكاء الاصطناعي         ║    ║
║   ╚════════════════════════════════════════════════════════════════════════════════╝    ║
║                                                                                          ║
║   🔧 HOW TO CHANGE MODELS | كيفية تغيير النماذج:                                        ║
║      1. Scroll down to "ACTIVE CONFIGURATION" section                                   ║
║      2. Change the model values directly                                                ║
║      3. Save the file and restart the application                                       ║
║                                                                                          ║
║      1. انزل إلى قسم "ACTIVE CONFIGURATION"                                             ║
║      2. غيّر قيم النماذج مباشرة                                                          ║
║      3. احفظ الملف وأعد تشغيل التطبيق                                                    ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

# ══════════════════════════════════════════════════════════════════════════════════════════
# 📋 AVAILABLE MODELS CATALOG | كتالوج النماذج المتاحة
# ══════════════════════════════════════════════════════════════════════════════════════════
# Reference only - Copy the model ID you want to use
# للمرجع فقط - انسخ معرف النموذج الذي تريد استخدامه


class AvailableModels:
    """
    📚 All Available AI Models | جميع النماذج المتاحة

    Copy the model ID (the string value) to use in the configuration below.
    انسخ معرف النموذج (القيمة النصية) لاستخدامه في التكوين أدناه.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # 🟢 OPENAI MODELS | نماذج OpenAI
    # ─────────────────────────────────────────────────────────────────────────
    GPT_4O = "openai/gpt-4o"  # 🏆 الأقوى، متعدد الوسائط
    GPT_4O_MINI = "openai/gpt-4o-mini"  # ⚡ سريع، موفر التكلفة
    GPT_4_TURBO = "openai/gpt-4-turbo"  # 🚀 GPT-4 محسّن
    GPT_4 = "openai/gpt-4"  # 📚 الكلاسيكي
    GPT_35_TURBO = "openai/gpt-3.5-turbo"  # 💨 سريع جداً، رخيص

    # ─────────────────────────────────────────────────────────────────────────
    # 🟣 ANTHROPIC MODELS | نماذج Anthropic
    # ─────────────────────────────────────────────────────────────────────────
    CLAUDE_37_SONNET_THINKING = "anthropic/claude-3.7-sonnet:thinking"  # 🧠 تفكير متقدم
    CLAUDE_35_SONNET = "anthropic/claude-3.5-sonnet"  # 🎯 استدلال ممتاز
    CLAUDE_3_OPUS = "anthropic/claude-3-opus"  # 🎓 الأكثر قدرة
    CLAUDE_3_HAIKU = "anthropic/claude-3-haiku"  # ⚡ سريع ورخيص

    # ─────────────────────────────────────────────────────────────────────────
    # 🔵 GOOGLE MODELS | نماذج Google
    # ─────────────────────────────────────────────────────────────────────────
    GEMINI_PRO = "google/gemini-pro"  # 🌟 الرئيسي
    GEMINI_PRO_15 = "google/gemini-pro-1.5"  # 🚀 الأحدث

    # ─────────────────────────────────────────────────────────────────────────
    # 🟠 META MODELS (Open Source) | نماذج Meta
    # ─────────────────────────────────────────────────────────────────────────
    LLAMA_3_70B = "meta-llama/llama-3-70b-instruct"  # 🔓 مفتوح المصدر قوي
    LLAMA_3_8B = "meta-llama/llama-3-8b-instruct"  # 💨 سريع ومجاني
    LLAMA_3_2_11B_VISION_FREE = "meta-llama/llama-3.2-11b-vision-instruct:free"  # 👁️ رؤية مجانية

    # ─────────────────────────────────────────────────────────────────────────
    # 🆓 FREE MODELS (High Quality) | نماذج مجانية عالية الجودة
    # ─────────────────────────────────────────────────────────────────────────
    GEMINI_2_FLASH_EXP_FREE = "google/gemini-2.0-flash-exp:free"  # ⚡ سريع جداً ومجاني
    PHI_3_MINI_FREE = "microsoft/phi-3-mini-128k-instruct:free"  # 🤏 صغير جداً ومجاني


# ══════════════════════════════════════════════════════════════════════════════════════════
#
#   ███████╗██████╗ ██╗████████╗    ██╗  ██╗███████╗██████╗ ███████╗
#   ██╔════╝██╔══██╗██║╚══██╔══╝    ██║  ██║██╔════╝██╔══██╗██╔════╝
#   █████╗  ██║  ██║██║   ██║       ███████║█████╗  ██████╔╝█████╗
#   ██╔══╝  ██║  ██║██║   ██║       ██╔══██║██╔══╝  ██╔══██╗██╔══╝
#   ███████╗██████╔╝██║   ██║       ██║  ██║███████╗██║  ██║███████╗
#   ╚══════╝╚═════╝ ╚═╝   ╚═╝       ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
#
#   👇👇👇 ACTIVE CONFIGURATION - EDIT BELOW TO CHANGE MODELS 👇👇👇
#   👇👇👇 التكوين النشط - عدّل أدناه لتغيير النماذج 👇👇👇
#
# ══════════════════════════════════════════════════════════════════════════════════════════


class ActiveModels:
    """
    ⚙️ ACTIVE AI MODELS CONFIGURATION | تكوين النماذج النشط

    ╔═══════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                   ║
    ║   🔧 TO CHANGE A MODEL:                                                          ║
    ║      1. Find the model you want to change below                                  ║
    ║      2. Replace the value with one from AvailableModels above                    ║
    ║      3. Save and restart                                                         ║
    ║                                                                                   ║
    ║   🔧 لتغيير نموذج:                                                               ║
    ║      1. ابحث عن النموذج الذي تريد تغييره أدناه                                   ║
    ║      2. استبدل القيمة بواحدة من AvailableModels أعلاه                            ║
    ║      3. احفظ وأعد التشغيل                                                        ║
    ║                                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════════════════════╝
    """

    # ═══════════════════════════════════════════════════════════════════════════════════
    # 🎯 PRIMARY MODEL | النموذج الرئيسي
    # ═══════════════════════════════════════════════════════════════════════════════════
    # This is the MAIN model used for most AI operations in the application.
    # هذا هو النموذج الرئيسي المستخدم لمعظم عمليات الذكاء الاصطناعي.
    #
    # 👉 CHANGE THIS to switch the main AI model
    # 👉 غيّر هذا لتبديل نموذج الذكاء الاصطناعي الرئيسي
    # ═══════════════════════════════════════════════════════════════════════════════════

    PRIMARY = "qwen/qwen3-coder:free"

    # ═══════════════════════════════════════════════════════════════════════════════════
    # 💰 LOW COST MODEL | نموذج منخفض التكلفة
    # ═══════════════════════════════════════════════════════════════════════════════════
    # Used for simple, quick tasks to save money.
    # يُستخدم للمهام البسيطة والسريعة لتوفير المال.
    # ═══════════════════════════════════════════════════════════════════════════════════

    LOW_COST = "deepseek/deepseek-v3.2-exp"

    # ═══════════════════════════════════════════════════════════════════════════════════
    # 🌟 GATEWAY MODELS | نماذج البوابة
    # ═══════════════════════════════════════════════════════════════════════════════════
    # Used by the Neural Routing Mesh for intelligent request routing.
    # تُستخدم من قبل شبكة التوجيه العصبي للتوجيه الذكي للطلبات.
    # ═══════════════════════════════════════════════════════════════════════════════════

    GATEWAY_PRIMARY = "qwen/qwen3-coder:free"  # Main gateway model
    GATEWAY_FALLBACK_1 = "google/gemini-2.0-flash-exp:free"  # First fallback (Gemini Flash 2.0)
    GATEWAY_FALLBACK_2 = "kwaipilot/kat-coder-pro:free"  # Second fallback (kwaipilot/kat-coder-pro)
    # ═══════════════════════════════════════════════════════════════════════════════════
    # ⚡ TIERED MODELS | النماذج المتدرجة
    # ═══════════════════════════════════════════════════════════════════════════════════
    # Different models for different complexity levels (intelligent routing).
    # نماذج مختلفة لمستويات تعقيد مختلفة (التوجيه الذكي).
    # ═══════════════════════════════════════════════════════════════════════════════════

    TIER_NANO = "openai/gpt-4o-mini"  # ⚡ Ultra-fast (<50ms) | فائق السرعة
    TIER_FAST = "openai/gpt-4o-mini"  # 🚀 Fast (<200ms) | سريع
    TIER_SMART = "anthropic/claude-3.5-sonnet"  # 🧠 Smart (<1s) | ذكي
    TIER_GENIUS = "anthropic/claude-3-opus"  # 🎓 Genius (<5s) | عبقري


# ══════════════════════════════════════════════════════════════════════════════════════════
#   👆👆👆 END OF CONFIGURATION - DO NOT EDIT BELOW THIS LINE 👆👆👆
#   👆👆👆 نهاية التكوين - لا تعدل أسفل هذا الخط 👆👆👆
# ══════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AIConfig:
    """
    AI Configuration singleton - reads from ActiveModels class.
    """

    # Primary
    primary_model: str = ActiveModels.PRIMARY
    low_cost_model: str = ActiveModels.LOW_COST

    # Gateway
    gateway_primary: str = ActiveModels.GATEWAY_PRIMARY
    gateway_fallback_1: str = ActiveModels.GATEWAY_FALLBACK_1
    gateway_fallback_2: str = ActiveModels.GATEWAY_FALLBACK_2

    # Tiers
    tier_nano: str = ActiveModels.TIER_NANO
    tier_fast: str = ActiveModels.TIER_FAST
    tier_smart: str = ActiveModels.TIER_SMART
    tier_genius: str = ActiveModels.TIER_GENIUS

    # API Keys (from environment - these ARE secrets)
    @property
    def openrouter_api_key(self) -> str | None:
        return os.getenv("OPENROUTER_API_KEY")

    @property
    def openai_api_key(self) -> str | None:
        return os.getenv("OPENAI_API_KEY")

    def get_fallback_models(self) -> list[str]:
        """Get list of fallback models."""
        return [self.gateway_fallback_1, self.gateway_fallback_2]

    def get_tier_model(self, tier: str) -> str:
        """Get model for a specific tier."""
        tier_map = {
            "nano": self.tier_nano,
            "fast": self.tier_fast,
            "smart": self.tier_smart,
            "genius": self.tier_genius,
        }
        return tier_map.get(tier.lower(), self.primary_model)

    def to_dict(self) -> dict:
        """Export configuration as dictionary."""
        return {
            "primary_model": self.primary_model,
            "low_cost_model": self.low_cost_model,
            "gateway": {
                "primary": self.gateway_primary,
                "fallback_1": self.gateway_fallback_1,
                "fallback_2": self.gateway_fallback_2,
            },
            "tiers": {
                "nano": self.tier_nano,
                "fast": self.tier_fast,
                "smart": self.tier_smart,
                "genius": self.tier_genius,
            },
        }

    def print_config(self) -> None:
        """Print current configuration."""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 CURRENT AI MODELS CONFIGURATION                        ║
╠══════════════════════════════════════════════════════════════════════════════╣""")
        print(f"║  🎯 Primary Model:     {self.primary_model:<50} ║")
        print(f"║  💰 Low Cost Model:    {self.low_cost_model:<50} ║")
        print("╠══════════════════════════════════════════════════════════════════════════════╣")
        print(f"║  🌟 Gateway Primary:   {self.gateway_primary:<50} ║")
        print(f"║  🔄 Fallback 1:        {self.gateway_fallback_1:<50} ║")
        print(f"║  🔄 Fallback 2:        {self.gateway_fallback_2:<50} ║")
        print("╠══════════════════════════════════════════════════════════════════════════════╣")
        print(f"║  ⚡ Tier NANO:         {self.tier_nano:<50} ║")
        print(f"║  🚀 Tier FAST:         {self.tier_fast:<50} ║")
        print(f"║  🧠 Tier SMART:        {self.tier_smart:<50} ║")
        print(f"║  🎓 Tier GENIUS:       {self.tier_genius:<50} ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝")


@lru_cache(maxsize=1)
def get_ai_config() -> AIConfig:
    """Get the AI configuration singleton."""
    return AIConfig()


# Singleton instance
ai_config = get_ai_config()


__all__ = [
    "AIConfig",
    "ActiveModels",
    "AvailableModels",
    "ai_config",
    "get_ai_config",
]


# ══════════════════════════════════════════════════════════════════════════════════════════
# 🧪 QUICK TEST | اختبار سريع
# ══════════════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n📋 Available Models for Reference:")
    print("─" * 60)
    print(f"  OpenAI GPT-4o:           {AvailableModels.GPT_4O}")
    print(f"  OpenAI GPT-4o-mini:      {AvailableModels.GPT_4O_MINI}")
    print(f"  Claude 3.7 Sonnet:       {AvailableModels.CLAUDE_37_SONNET_THINKING}")
    print(f"  Claude 3.5 Sonnet:       {AvailableModels.CLAUDE_35_SONNET}")
    print(f"  Claude 3 Opus:           {AvailableModels.CLAUDE_3_OPUS}")
    print("─" * 60)

    config = get_ai_config()
    config.print_config()
