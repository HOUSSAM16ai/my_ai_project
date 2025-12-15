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
║              🧠 AI MODELS CONFIGURATION CENTER v2.1 - SUPERHUMAN EDITION                ║
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


class AvailableModels:
    """
    📚 All Available AI Models | جميع النماذج المتاحة

    Copy the model ID (the string value) to use in the configuration below.
    انسخ معرف النموذج (القيمة النصية) لاستخدامه في التكوين أدناه.
    """
    GPT_4O = 'openai/gpt-4o'
    GPT_4O_MINI = 'openai/gpt-4o-mini'
    GPT_4_TURBO = 'openai/gpt-4-turbo'
    GPT_4 = 'openai/gpt-4'
    GPT_35_TURBO = 'openai/gpt-3.5-turbo'
    CLAUDE_37_SONNET_THINKING = 'anthropic/claude-3.7-sonnet:thinking'
    CLAUDE_35_SONNET = 'anthropic/claude-3.5-sonnet'
    CLAUDE_OPUS_4_5 = 'anthropic/claude-opus-4.5'
    CLAUDE_3_OPUS = 'anthropic/claude-3-opus'
    CLAUDE_3_HAIKU = 'anthropic/claude-3-haiku'
    GEMINI_PRO = 'google/gemini-pro'
    GEMINI_PRO_15 = 'google/gemini-pro-1.5'
    LLAMA_3_70B = 'meta-llama/llama-3-70b-instruct'
    LLAMA_3_8B = 'meta-llama/llama-3-8b-instruct'
    LLAMA_3_2_11B_VISION_FREE = 'meta-llama/llama-3.2-11b-vision-instruct:free'
    GEMINI_2_FLASH_EXP_FREE = 'google/gemini-2.0-flash-exp:free'
    PHI_3_MINI_FREE = 'microsoft/phi-3-mini-128k-instruct:free'
    KAT_CODER_PRO_FREE = 'kwaipilot/kat-coder-pro:free'
    QWEN_QWEN3_CODER_FREE = 'qwen/qwen3-coder:free'


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
    PRIMARY = AvailableModels.CLAUDE_OPUS_4_5
    LOW_COST = 'deepseek/deepseek-v3.2-exp'
    GATEWAY_PRIMARY = AvailableModels.CLAUDE_OPUS_4_5
    GATEWAY_FALLBACK_1 = AvailableModels.GEMINI_2_FLASH_EXP_FREE
    GATEWAY_FALLBACK_2 = AvailableModels.QWEN_QWEN3_CODER_FREE
    GATEWAY_FALLBACK_3 = AvailableModels.KAT_CODER_PRO_FREE
    GATEWAY_FALLBACK_4 = AvailableModels.PHI_3_MINI_FREE
    GATEWAY_FALLBACK_5 = AvailableModels.LLAMA_3_2_11B_VISION_FREE
    TIER_NANO = AvailableModels.GPT_4O_MINI
    TIER_FAST = AvailableModels.GPT_4O_MINI
    TIER_SMART = AvailableModels.CLAUDE_35_SONNET
    TIER_GENIUS = AvailableModels.CLAUDE_3_OPUS


@dataclass(frozen=True)
class AIConfig:
    """
    AI Configuration singleton - reads from ActiveModels class.
    """
    primary_model: str = ActiveModels.PRIMARY
    low_cost_model: str = ActiveModels.LOW_COST
    gateway_primary: str = ActiveModels.GATEWAY_PRIMARY
    gateway_fallback_1: str = ActiveModels.GATEWAY_FALLBACK_1
    gateway_fallback_2: str = ActiveModels.GATEWAY_FALLBACK_2
    gateway_fallback_3: str = ActiveModels.GATEWAY_FALLBACK_3
    gateway_fallback_4: str = ActiveModels.GATEWAY_FALLBACK_4
    gateway_fallback_5: str = ActiveModels.GATEWAY_FALLBACK_5
    tier_nano: str = ActiveModels.TIER_NANO
    tier_fast: str = ActiveModels.TIER_FAST
    tier_smart: str = ActiveModels.TIER_SMART
    tier_genius: str = ActiveModels.TIER_GENIUS

    @property
    def openrouter_api_key(self) ->(str | None):
        return os.getenv('OPENROUTER_API_KEY')

    def get_fallback_models(self) ->list[str]:
        """Get list of fallback models."""
        return [self.gateway_fallback_1, self.gateway_fallback_2, self.
            gateway_fallback_3, self.gateway_fallback_4, self.
            gateway_fallback_5]

    def to_dict(self) ->dict:
        """Export configuration as dictionary."""
        return {'primary_model': self.primary_model, 'low_cost_model': self
            .low_cost_model, 'gateway': {'primary': self.gateway_primary,
            'fallback_1': self.gateway_fallback_1, 'fallback_2': self.
            gateway_fallback_2, 'fallback_3': self.gateway_fallback_3,
            'fallback_4': self.gateway_fallback_4, 'fallback_5': self.
            gateway_fallback_5}, 'tiers': {'nano': self.tier_nano, 'fast':
            self.tier_fast, 'smart': self.tier_smart, 'genius': self.
            tier_genius}}

    def print_config(self) ->None:
        """Print current configuration."""
        print(
            """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 CURRENT AI MODELS CONFIGURATION                        ║
╠══════════════════════════════════════════════════════════════════════════════╣"""
            )
        print(f'║  🎯 Primary Model:     {self.primary_model:<50} ║')
        print(f'║  💰 Low Cost Model:    {self.low_cost_model:<50} ║')
        print(
            '╠══════════════════════════════════════════════════════════════════════════════╣'
            )
        print(f'║  🌟 Gateway Primary:   {self.gateway_primary:<50} ║')
        print(f'║  🔄 Fallback 1:        {self.gateway_fallback_1:<50} ║')
        print(f'║  🔄 Fallback 2:        {self.gateway_fallback_2:<50} ║')
        print(f'║  🔄 Fallback 3:        {self.gateway_fallback_3:<50} ║')
        print(f'║  🔄 Fallback 4:        {self.gateway_fallback_4:<50} ║')
        print(f'║  🔄 Fallback 5:        {self.gateway_fallback_5:<50} ║')
        print(
            '╠══════════════════════════════════════════════════════════════════════════════╣'
            )
        print(f'║  ⚡ Tier NANO:         {self.tier_nano:<50} ║')
        print(f'║  🚀 Tier FAST:         {self.tier_fast:<50} ║')
        print(f'║  🧠 Tier SMART:        {self.tier_smart:<50} ║')
        print(f'║  🎓 Tier GENIUS:       {self.tier_genius:<50} ║')
        print(
            '╚══════════════════════════════════════════════════════════════════════════════╝'
            )


@lru_cache(maxsize=1)
def get_ai_config() ->AIConfig:
    """Get the AI configuration singleton."""
    return AIConfig()


ai_config = get_ai_config()
__all__ = ['AIConfig', 'ActiveModels', 'AvailableModels', 'ai_config',
    'get_ai_config']
if __name__ == '__main__':
    print('\n📋 Available Models for Reference:')
    print('─' * 60)
    print(f'  OpenAI GPT-4o:           {AvailableModels.GPT_4O}')
    print(f'  OpenAI GPT-4o-mini:      {AvailableModels.GPT_4O_MINI}')
    print(
        f'  Claude 3.7 Sonnet:       {AvailableModels.CLAUDE_37_SONNET_THINKING}'
        )
    print(f'  Claude 3.5 Sonnet:       {AvailableModels.CLAUDE_35_SONNET}')
    print(f'  Claude 3 Opus:           {AvailableModels.CLAUDE_3_OPUS}')
    print('─' * 60)
    config = get_ai_config()
    config.print_config()
