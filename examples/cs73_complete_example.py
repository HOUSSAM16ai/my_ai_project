#!/usr/bin/env python3
"""
🎨 CS73 Complete Usage Example
==============================

This example demonstrates the full capabilities of the CS73 implementation,
showing how to transform various types of Overmind data into beautiful art.

Run: python3 examples/cs73_complete_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.overmind.art.integration import (
    OvermindArtIntegration,
    create_art_from_overmind_data,
)
from app.services.overmind.art.styles import ArtStyle, VisualTheme


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"🎨 {title}")
    print("=" * 70)


def example_1_color_theory():
    """Example 1: Understanding Color Theory"""
    print_section("Example 1: Color Theory & Palettes")

    print("\n📚 Available Art Styles:")
    for style in ArtStyle:
        palette = VisualTheme.get_palette(style)
        print(
            f"  • {style.value:12s} - Primary: {palette.primary}, Background: {palette.background}"
        )

    print("\n🌈 Creating Color Gradients:")
    gradient = VisualTheme.create_gradient("#FF0000", "#0000FF", steps=5)
    print(f"  Red → Blue gradient: {' → '.join(gradient)}")

    print("\n🔍 Contrast Calculation:")
    for color in ["#FFFFFF", "#000000", "#808080"]:
        contrast = VisualTheme.get_contrasting_color(color)
        print(f"  Background {color} → Text {contrast}")


def example_2_code_complexity():
    """Example 2: Visualizing Code Complexity"""
    print_section("Example 2: Code Complexity as Art")

    # Simulated code analysis data
    analysis_data = {
        "avg_complexity": 6.8,
        "max_complexity": 18,
        "functions": 127,
        "classes": 34,
        "lines": 4582,
        "maintainability_index": 72.5,
    }

    print("\n📊 Analysis Data:")
    for key, value in analysis_data.items():
        print(f"  • {key}: {value}")

    # Create visualizations in different styles
    print("\n🎭 Generating Art in 3 Different Styles...")

    for style in [ArtStyle.CYBERPUNK, ArtStyle.NATURE, ArtStyle.MODERN]:
        integration = OvermindArtIntegration(style)
        art = integration.visualize_code_intelligence(analysis_data)

        print(f"\n  {style.value.upper()}:")
        print(f"    ✓ Complexity art: {len(art['complexity_art'])} chars")
        print(f"    ✓ Metrics dashboard: {len(art['metrics_dashboard'])} chars")
        print(f"    ✓ Code pattern: {len(art['pattern_art'])} chars")
        print(f"    ✓ Fractal tree: {len(art['fractal_tree'])} chars")


def example_3_mission_timeline():
    """Example 3: Mission Journey Visualization"""
    print_section("Example 3: Mission Journey Timeline")

    mission_data = {
        "id": 42,
        "name": "Implement CS73",
        "events": [
            {"name": "Planning", "type": "start", "timestamp": "2026-01-02T10:00:00"},
            {"name": "Design", "type": "info", "timestamp": "2026-01-02T11:00:00"},
            {"name": "Implementation", "type": "info", "timestamp": "2026-01-02T13:00:00"},
            {"name": "Testing", "type": "warning", "timestamp": "2026-01-02T15:00:00"},
            {"name": "Documentation", "type": "info", "timestamp": "2026-01-02T16:00:00"},
            {"name": "Complete", "type": "success", "timestamp": "2026-01-02T17:00:00"},
        ],
    }

    print(f"\n📋 Mission: {mission_data['name']}")
    print(f"  Events: {len(mission_data['events'])}")

    integration = OvermindArtIntegration(ArtStyle.GRADIENT)
    art = integration.visualize_mission_journey(mission_data)

    print("\n🎨 Generated Art:")
    print(f"  ✓ Timeline: {len(art['timeline'])} chars")
    print(f"  ✓ Evolution spiral: {len(art['evolution_spiral'])} chars")


def example_4_metrics_art():
    """Example 4: Metrics Visualization"""
    print_section("Example 4: Metrics as Art")

    metrics = {
        "code_quality": 8.7,
        "performance": 9.2,
        "maintainability": 7.8,
        "security": 8.5,
        "documentation": 9.1,
        "test_coverage": 85.3,
        "type_safety": 100.0,
    }

    print("\n📊 Metrics:")
    for key, value in metrics.items():
        print(f"  • {key}: {value}")

    integration = OvermindArtIntegration(ArtStyle.DARK)

    print("\n🎨 Generating Multiple Visualization Types...")
    art = integration.visualize_metrics(metrics, visualization_types=["radial", "bar", "sculpture"])

    print(f"  ✓ Radial chart: {len(art['radial_chart'])} chars")
    print(f"  ✓ Bar chart: {len(art['bar_chart'])} chars")
    print(f"  ✓ Data sculpture: {len(art['data_sculpture'])} chars")


def example_5_dependency_network():
    """Example 5: Dependency Network Visualization"""
    print_section("Example 5: Code Dependencies as Network Art")

    modules = [
        "authentication",
        "users",
        "database",
        "api",
        "services",
        "middleware",
        "admin",
        "overmind",
        "art_system",
    ]

    dependencies = [
        ("users", "authentication"),
        ("users", "database"),
        ("api", "users"),
        ("api", "services"),
        ("api", "middleware"),
        ("services", "database"),
        ("admin", "users"),
        ("admin", "api"),
        ("overmind", "services"),
        ("overmind", "database"),
        ("art_system", "overmind"),
    ]

    print(f"\n📦 Modules: {len(modules)}")
    print(f"🔗 Dependencies: {len(dependencies)}")

    integration = OvermindArtIntegration(ArtStyle.RETRO)
    network = integration.visualize_dependencies(modules, dependencies)

    print(f"\n🎨 Network Visualization: {len(network)} chars")
    print("  ✓ Circular node layout")
    print("  ✓ Connection lines")
    print("  ✓ Color-coded modules")


def example_6_generative_art():
    """Example 6: Pure Generative Art"""
    print_section("Example 6: Algorithmic Generative Art")

    from app.services.overmind.art.generators import CodePatternArtist

    artist = CodePatternArtist(ArtStyle.CYBERPUNK)

    print("\n🌳 Fractal Tree Generation:")
    for depth in [3, 4, 5, 6]:
        fractal = artist.generate_fractal_tree(complexity=depth, seed=42)
        branches = 2**depth
        print(f"  Depth {depth}: ~{branches} branches, {len(fractal)} chars")

    print("\n🌀 Evolution Spiral:")
    for iterations in [50, 100, 200]:
        spiral = artist.generate_spiral_code(iterations=iterations)
        print(f"  {iterations} iterations: {len(spiral)} chars")


def example_7_full_report():
    """Example 7: Complete Art Report"""
    print_section("Example 7: Full Overmind Art Report")

    # Comprehensive Overmind data
    overmind_data = {
        "code_analysis": {
            "avg_complexity": 5.4,
            "max_complexity": 16,
            "functions": 156,
            "classes": 42,
            "lines": 5234,
        },
        "mission_data": {
            "id": 999,
            "events": [
                {"name": "Start", "type": "start"},
                {"name": "Analysis", "type": "info"},
                {"name": "Implementation", "type": "info"},
                {"name": "Success", "type": "success"},
            ],
        },
        "metrics": {"quality": 9.1, "performance": 8.8, "security": 9.0, "maintainability": 8.5},
        "dependencies": {
            "modules": ["core", "api", "services", "art"],
            "edges": [("api", "core"), ("services", "core"), ("art", "services")],
        },
    }

    print("\n📦 Creating comprehensive art report...")
    report = create_art_from_overmind_data(overmind_data, ArtStyle.GRADIENT)

    print("\n✅ Report Generated:")
    print(f"  🎨 Style: {report['style']}")
    print(f"  📊 Sections: {len(report['visualizations'])}")

    total_chars = 0
    for section, content in report["visualizations"].items():
        if isinstance(content, dict):
            section_chars = sum(len(str(v)) for v in content.values())
            print(f"    • {section}: {len(content)} visualizations ({section_chars} chars)")
        else:
            print(f"    • {section}: {len(str(content))} chars")
        total_chars += section_chars if isinstance(content, dict) else len(str(content))

    print(f"\n  📝 Total output: {total_chars:,} characters of art!")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("🎨 CS73: Code, Data, and Art - Complete Examples")
    print("   Harvard CS73 Implementation on Overmind")
    print("=" * 70)

    try:
        example_1_color_theory()
        example_2_code_complexity()
        example_3_mission_timeline()
        example_4_metrics_art()
        example_5_dependency_network()
        example_6_generative_art()
        example_7_full_report()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("\n💡 Next Steps:")
        print("  1. Check docs/CS73_IMPLEMENTATION_GUIDE.md for full API reference")
        print("  2. Run: python3 examples/cs73_demo.py for quick demo")
        print("  3. Integrate with your Overmind analysis pipelines")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
