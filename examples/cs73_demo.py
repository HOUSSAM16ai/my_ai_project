#!/usr/bin/env python3
"""
🎨 CS73 Demo: Code, Data, and Art
==================================

هذا الملف يوضح استخدام نظام CS73 المطبق على Overmind.
يعرض أمثلة عملية لتحويل البيانات البرمجية إلى فن.

Usage:
    python3 examples/cs73_demo.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.overmind.art.integration import (
    OvermindArtIntegration,
)
from app.services.overmind.art.styles import ArtStyle


def demo_all_styles():
    """عرض جميع الأنماط الفنية"""
    print("\n" + "=" * 60)
    print("🎨 CS73: All Art Styles Demo")
    print("=" * 60)

    analysis = {"avg_complexity": 5.2, "max_complexity": 15, "functions": 42, "classes": 12}

    for style in ArtStyle:
        print(f"\n  🎭 Style: {style.value}")
        integration = OvermindArtIntegration(style)
        visualizations = integration.visualize_code_intelligence(analysis)
        print(f"     ✓ Created {len(visualizations)} visualizations")


def main():
    """نقطة الدخول الرئيسية"""
    print("\n" + "=" * 60)
    print("🎨 CS73: Code, Data, and Art - Quick Demo")
    print("   Harvard CS73 Implementation on Overmind")
    print("=" * 60)

    try:
        demo_all_styles()

        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
