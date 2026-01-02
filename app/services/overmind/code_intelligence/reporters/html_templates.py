"""
قوالب HTML للتقارير | HTML Templates for Reports.

هذا الملف يحتوي على جميع قوالب HTML المستخدمة في تقارير تحليل الكود.
فصل القوالب عن منطق البرمجة يجعل الكود أنظف وأسهل في الصيانة.

المبادئ المطبقة:
- Separation of Concerns: فصل العرض (Presentation) عن المنطق (Logic)
- DRY: قوالب قابلة لإعادة الاستخدام
- KISS: قوالب بسيطة وواضحة
"""

from typing import Any


def get_html_styles() -> str:
    """
    الحصول على أنماط CSS للتقرير.
    
    Returns:
        str: كود CSS كامل
        
    ملاحظة: كل قاعدة CSS موثقة لتوضيح الغرض منها
    """
    return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;  /* خلفية داكنة للراحة البصرية */
            color: #e0e0e0;       /* نص فاتح للتباين */
            padding: 20px;        /* مسافة حول المحتوى */
            direction: rtl;       /* اتجاه النص من اليمين لليسار */
        }
        .container {
            max-width: 1400px;    /* عرض أقصى للقراءة المريحة */
            margin: 0 auto;       /* توسيط المحتوى */
        }
        h1 {
            color: #00d4ff;       /* لون مميز للعنوان الرئيسي */
            text-align: center;
            margin-bottom: 10px;
        }
        .summary {
            background: #2a2a2a;  /* خلفية أفتح قليلاً */
            padding: 20px;
            border-radius: 8px;   /* زوايا مستديرة */
            margin-bottom: 30px;
            border-left: 4px solid #00d4ff;  /* شريط جانبي مميز */
        }
        .summary h2 {
            margin-top: 0;
            color: #00d4ff;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));  /* شبكة متجاوبة */
            gap: 15px;
            margin-top: 15px;
        }
        .stat {
            background: #1a1a1a;
            padding: 15px;
            border-radius: 6px;
        }
        .stat-label {
            color: #888;          /* لون أغمق للتسميات */
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;       /* لون مميز للقيم */
        }
        .heatmap {
            display: grid;
            gap: 10px;
        }
        .file-row {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 6px;
            border-right: 6px solid;  /* الشريط الجانبي الملون */
            transition: transform 0.2s;  /* حركة سلسة عند التفاعل */
        }
        .file-row:hover {
            transform: translateX(-5px);  /* حركة طفيفة عند المرور */
            box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);  /* ظل توضيحي */
        }
        /* ألوان حسب مستوى الخطورة */
        .file-row.critical {
            border-right-color: #ff4444;  /* أحمر للحرج */
            background: linear-gradient(90deg, #2a2a2a 0%, #3a1a1a 100%);
        }
        .file-row.high {
            border-right-color: #ff9944;  /* برتقالي للعالي */
            background: linear-gradient(90deg, #2a2a2a 0%, #3a2a1a 100%);
        }
        .file-row.medium {
            border-right-color: #ffdd44;  /* أصفر للمتوسط */
            background: linear-gradient(90deg, #2a2a2a 0%, #3a3a1a 100%);
        }
        .file-row.low {
            border-right-color: #44ff44;  /* أخضر للمنخفض */
            background: linear-gradient(90deg, #2a2a2a 0%, #1a3a1a 100%);
        }
        .file-name {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #fff;
        }
        .file-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
        }
        .metric-label {
            color: #888;
        }
        .metric-value {
            color: #00d4ff;
            font-weight: bold;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 8px;
        }
        .badge.critical {
            background: #ff4444;
            color: white;
        }
        .badge.high {
            background: #ff9944;
            color: white;
        }
        .badge.medium {
            background: #ffdd44;
            color: black;
        }
        .badge.low {
            background: #44ff44;
            color: black;
        }
        .legend {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .legend-items {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 30px;
            height: 20px;
            border-radius: 4px;
        }
    """


def create_file_row_html(
    relative_path: str,
    priority_tier: str,
    hotspot_score: float,
    file_complexity: int,
    code_lines: int,
    num_functions: int,
    commits_last_12months: int,
    bugfix_commits: int,
    smells_html: str,
) -> str:
    """
    إنشاء HTML لصف ملف واحد في الخريطة الحرارية.
    
    Args:
        relative_path: المسار النسبي للملف
        priority_tier: مستوى الأولوية (Critical, High, Medium, Low)
        hotspot_score: درجة الخطورة (0.0 - 1.0)
        file_complexity: التعقيد الكلي للملف
        code_lines: عدد أسطر الكود
        num_functions: عدد الدوال
        commits_last_12months: عدد التعديلات في آخر 12 شهر
        bugfix_commits: عدد commits إصلاح الأخطاء
        smells_html: الروائح البنيوية (HTML formatted)
        
    Returns:
        str: HTML كامل لصف الملف
        
    ملاحظة: كل معامل له دور واضح في بناء التقرير
    """
    tier_class = priority_tier.lower()  # تحويل إلى lowercase لاستخدامه كـ CSS class
    
    return f"""
        <div class="file-row {tier_class}">
            <div class="file-name">
                <span class="badge {tier_class}">{priority_tier}</span>
                {relative_path}
            </div>
            <div class="file-metrics">
                <div class="metric">
                    <span class="metric-label">درجة الخطورة:</span>
                    <span class="metric-value">{hotspot_score:.4f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">التعقيد الكلي:</span>
                    <span class="metric-value">{file_complexity}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">أسطر الكود:</span>
                    <span class="metric-value">{code_lines}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">الدوال:</span>
                    <span class="metric-value">{num_functions}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">التعديلات (12 شهر):</span>
                    <span class="metric-value">{commits_last_12months}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">إصلاحات الأخطاء:</span>
                    <span class="metric-value">{bugfix_commits}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">الروائح البنيوية:</span>
                    <span class="metric-value">{smells_html}</span>
                </div>
            </div>
        </div>"""


def create_complete_html(
    timestamp: str,
    total_files: int,
    total_code_lines: int,
    total_functions: int,
    total_classes: int,
    avg_file_complexity: float,
    max_file_complexity: int,
    file_rows_html: str,
) -> str:
    """
    إنشاء HTML كامل للتقرير.
    
    Args:
        timestamp: وقت إنشاء التقرير
        total_files: إجمالي عدد الملفات
        total_code_lines: إجمالي أسطر الكود
        total_functions: إجمالي عدد الدوال
        total_classes: إجمالي عدد الكلاسات
        avg_file_complexity: متوسط التعقيد
        max_file_complexity: أقصى تعقيد
        file_rows_html: HTML لجميع صفوف الملفات (مجمّعة)
        
    Returns:
        str: مستند HTML كامل
        
    ملاحظة: كل قوس وفاصلة في f-string لها دور محدد
    """
    styles = get_html_styles()
    
    # بناء المستند HTML الكامل
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خريطة حرارية - التحليل البنيوي للكود</title>
    <style>{styles}</style>
</head>
<body>
    <div class="container">
        <h1>🔥 خريطة حرارية - التحليل البنيوي للكود</h1>
        <p style="text-align: center; color: #888;">تم الإنشاء: {timestamp}</p>

        <div class="summary">
            <h2>📊 ملخص المشروع</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">إجمالي الملفات</div>
                    <div class="stat-value">{total_files}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">أسطر الكود</div>
                    <div class="stat-value">{total_code_lines:,}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">إجمالي الدوال</div>
                    <div class="stat-value">{total_functions}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">إجمالي الكلاسات</div>
                    <div class="stat-value">{total_classes}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">متوسط التعقيد</div>
                    <div class="stat-value">{avg_file_complexity:.1f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">أقصى تعقيد</div>
                    <div class="stat-value">{max_file_complexity}</div>
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
            {file_rows_html}
        </div>
    </div>
</body>
</html>"""
