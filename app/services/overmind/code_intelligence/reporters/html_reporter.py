from pathlib import Path

from ..models import ProjectAnalysis

# TODO: Split this function (282 lines) - KISS principle
def generate_heatmap_html(analysis: ProjectAnalysis, output_path: Path) -> None:
    """Generate HTML heatmap"""

    # Build file rows HTML
    file_rows_html = []
    for file_metrics in analysis.files[:50]:  # Top 50 files
        tier_class = file_metrics.priority_tier.lower()
        smells = []
        if file_metrics.is_god_class:
            smells.append("God Class")
        if file_metrics.has_layer_mixing:
            smells.append("Layer Mixing")
        if file_metrics.has_cross_layer_imports:
            smells.append("Cross-Layer Imports")

        smells_html = ", ".join(smells) if smells else "لا توجد"

        row_html = f"""
            <div class="file-row {tier_class}">
                <div class="file-name">
                    <span class="badge {tier_class}">{file_metrics.priority_tier}</span>
                    {file_metrics.relative_path}
                </div>
                <div class="file-metrics">
                    <div class="metric">
                        <span class="metric-label">درجة الخطورة:</span>
                        <span class="metric-value">{file_metrics.hotspot_score:.4f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">التعقيد الكلي:</span>
                        <span class="metric-value">{file_metrics.file_complexity}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">أسطر الكود:</span>
                        <span class="metric-value">{file_metrics.code_lines}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">الدوال:</span>
                        <span class="metric-value">{file_metrics.num_functions}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">التعديلات (12 شهر):</span>
                        <span class="metric-value">{file_metrics.commits_last_12months}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">إصلاحات الأخطاء:</span>
                        <span class="metric-value">{file_metrics.bugfix_commits}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">الروائح البنيوية:</span>
                        <span class="metric-value">{smells_html}</span>
                    </div>
                </div>
            </div>"""
        file_rows_html.append(row_html)

    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خريطة حرارية - التحليل البنيوي للكود</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            direction: rtl;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00d4ff;
            text-align: center;
            margin-bottom: 10px;
        }}
        .summary {{
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #00d4ff;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #00d4ff;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat {{
            background: #1a1a1a;
            padding: 15px;
            border-radius: 6px;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
        }}
        .heatmap {{
            display: grid;
            gap: 10px;
        }}
        .file-row {{
            background: #2a2a2a;
            padding: 15px;
            border-radius: 6px;
            border-right: 6px solid;
            transition: transform 0.2s;
        }}
        .file-row:hover {{
            transform: translateX(-5px);
            box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
        }}
        .file-row.critical {{
            border-right-color: #ff4444;
            background: linear-gradient(90deg, #2a2a2a 0%, #3a1a1a 100%);
        }}
        .file-row.high {{
            border-right-color: #ff9944;
            background: linear-gradient(90deg, #2a2a2a 0%, #3a2a1a 100%);
        }}
        .file-row.medium {{
            border-right-color: #ffdd44;
            background: linear-gradient(90deg, #2a2a2a 0%, #3a3a1a 100%);
        }}
        .file-row.low {{
            border-right-color: #44ff44;
            background: linear-gradient(90deg, #2a2a2a 0%, #1a3a1a 100%);
        }}
        .file-name {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #fff;
        }}
        .file-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
        }}
        .metric-label {{
            color: #888;
        }}
        .metric-value {{
            color: #00d4ff;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 8px;
        }}
        .badge.critical {{
            background: #ff4444;
            color: white;
        }}
        .badge.high {{
            background: #ff9944;
            color: white;
        }}
        .badge.medium {{
            background: #ffdd44;
            color: black;
        }}
        .badge.low {{
            background: #44ff44;
            color: black;
        }}
        .legend {{
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .legend-items {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 30px;
            height: 20px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 خريطة حرارية - التحليل البنيوي للكود</h1>
        <p style="text-align: center; color: #888;">تم الإنشاء: {analysis.timestamp}</p>

        <div class="summary">
            <h2>📊 ملخص المشروع</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">إجمالي الملفات</div>
                    <div class="stat-value">{analysis.total_files}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">أسطر الكود</div>
                    <div class="stat-value">{analysis.total_code_lines:,}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">إجمالي الدوال</div>
                    <div class="stat-value">{analysis.total_functions}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">إجمالي الكلاسات</div>
                    <div class="stat-value">{analysis.total_classes}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">متوسط التعقيد</div>
                    <div class="stat-value">{analysis.avg_file_complexity:.1f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">أقصى تعقيد</div>
                    <div class="stat-value">{analysis.max_file_complexity}</div>
                </div>
            </div>
        </div>

        <div class="legend">
            <h3>دليل الألوان</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff4444;"></div>
                    <span>حرج (≥0.7)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff9944;"></div>
                    <span>عالي (≥0.5)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffdd44;"></div>
                    <span>متوسط (≥0.3)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #44ff44;"></div>
                    <span>منخفض (&lt;0.3)</span>
                </div>
            </div>
        </div>

        <div class="heatmap">
            {"".join(file_rows_html)}
        </div>
    </div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"💾 Heatmap HTML saved: {output_path}")
