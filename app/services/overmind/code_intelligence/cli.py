import argparse
from datetime import datetime
from pathlib import Path

from .core import StructuralCodeIntelligence
from .reporters.csv_reporter import save_csv_report
from .reporters.html_reporter import generate_heatmap_html
from .reporters.json_reporter import save_json_report
from .reporters.markdown_reporter import generate_markdown_report

# TODO: Split this function (54 lines) - KISS principle
def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="المرحلة الأولى: التحليل الكمي البنيوي لقاعدة الشيفرة\nPhase 1: Structural Code Intelligence Analysis (Deconstructed)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=Path.cwd(),
        help="Repository path (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/structural_analysis"),
        help="Report output directory",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=["app/api", "app/services", "app/infrastructure", "app/application/use_cases"],
        help="Target paths for analysis",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run analysis
    analyzer = StructuralCodeIntelligence(args.repo_path, args.targets)
    analysis = analyzer.analyze_project()

    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n📝 Generating reports...")
    save_json_report(analysis, args.output_dir / f"structural_analysis_{timestamp}.json")
    save_csv_report(analysis, args.output_dir / f"structural_analysis_{timestamp}.csv")
    generate_heatmap_html(analysis, args.output_dir / f"heatmap_{timestamp}.html")
    generate_markdown_report(analysis, args.output_dir / f"report_{timestamp}.md")

    # Also save as latest
    save_json_report(analysis, args.output_dir / "structural_analysis_latest.json")
    save_csv_report(analysis, args.output_dir / "structural_analysis_latest.csv")
    generate_heatmap_html(analysis, args.output_dir / "heatmap_latest.html")
    generate_markdown_report(analysis, args.output_dir / "report_latest.md")

    print("\n✅ Analysis complete!")
    print("\n📊 Summary:")
    print(f"  - Files analyzed: {analysis.total_files}")
    print(f"  - Critical hotspots: {len(analysis.critical_hotspots)}")
    print(f"  - High hotspots: {len(analysis.high_hotspots)}")
    print(f"\n📁 Reports saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
