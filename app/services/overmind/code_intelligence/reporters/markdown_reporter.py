from collections import defaultdict
from pathlib import Path

from ..models import ProjectAnalysis


def generate_markdown_report(analysis: ProjectAnalysis, output_path: Path) -> None:
    """Generate Markdown report"""
    md = f"""# 🔍 تقرير التحليل البنيوي للكود
**Phase 1: Structural Code Intelligence Analysis**

تم الإنشاء: {analysis.timestamp}

---

## 📊 ملخص المشروع

| المقياس | القيمة |
|---------|--------|
| إجمالي الملفات المحللة | {analysis.total_files} |
| إجمالي الأسطر | {analysis.total_lines:,} |
| أسطر الكود (LOC) | {analysis.total_code_lines:,} |
| إجمالي الدوال | {analysis.total_functions} |
| إجمالي الكلاسات | {analysis.total_classes} |
| متوسط التعقيد للملف | {analysis.avg_file_complexity:.2f} |
| أقصى تعقيد للملف | {analysis.max_file_complexity} |

---

## 🔥 Hotspots حرجة (Top 20)

الملفات التي تحتاج إلى معالجة فورية:

"""

    for i, path in enumerate(analysis.critical_hotspots, 1):
        # Find the file metrics
        file_m = next((f for f in analysis.files if f.relative_path == path), None)
        if file_m:
            md += f"{i}. **{path}**\n"
            md += f"   - درجة الخطورة: `{file_m.hotspot_score:.4f}` | "
            md += f"التعقيد: `{file_m.file_complexity}` | "
            md += f"التعديلات: `{file_m.commits_last_12months}` | "
            md += f"الأولوية: `{file_m.priority_tier}`\n\n"

    md += "\n---\n\n## ⚠️ Hotspots عالية (التالي 20)\n\n"

    for i, path in enumerate(analysis.high_hotspots, 1):
        file_m = next((f for f in analysis.files if f.relative_path == path), None)
        if file_m:
            md += f"{i}. **{path}** - درجة: `{file_m.hotspot_score:.4f}`\n"

    md += "\n---\n\n## 📈 توزيع الأولويات\n\n"

    # Count by priority
    priority_counts = defaultdict(int)
    for f in analysis.files:
        priority_counts[f.priority_tier] += 1

    md += f"- 🔴 حرجة (CRITICAL): {priority_counts['CRITICAL']}\n"
    md += f"- 🟠 عالية (HIGH): {priority_counts['HIGH']}\n"
    md += f"- 🟡 متوسطة (MEDIUM): {priority_counts['MEDIUM']}\n"
    md += f"- 🟢 منخفضة (LOW): {priority_counts['LOW']}\n"

    md += "\n---\n\n## 🦨 الروائح البنيوية المكتشفة\n\n"

    god_classes = [f for f in analysis.files if f.is_god_class]
    layer_mixing = [f for f in analysis.files if f.has_layer_mixing]
    cross_layer = [f for f in analysis.files if f.has_cross_layer_imports]

    md += f"- **God Classes**: {len(god_classes)} ملف\n"
    md += f"- **Layer Mixing**: {len(layer_mixing)} ملف\n"
    md += f"- **Cross-Layer Imports**: {len(cross_layer)} ملف\n"

    md += "\n---\n\n## 📋 الخطوات التالية\n\n"
    md += "بناءً على هذا التحليل، يُوصى بالبدء في معالجة الملفات الحرجة أولاً:\n\n"
    md += "1. تطبيق مبدأ المسؤولية الواحدة (SRP) على God Classes\n"
    md += "2. إعادة التقسيم الطبقي للملفات ذات Layer Mixing\n"
    md += "3. عكس التبعيات غير الصحيحة (Cross-Layer Imports)\n"
    md += "4. تبسيط الدوال عالية التعقيد\n"
    md += "5. تحسين الملفات الأكثر تعديلاً لتقليل الأخطاء المستقبلية\n"

    md += "\n---\n\n## 📝 ملاحظات\n\n"
    md += "- هذا التقرير يمثل baseline للمشروع الحالي\n"
    md += "- يجب استخدامه كمرجع لقياس التحسينات بعد تطبيق SOLID\n"
    md += "- جميع المقاييس قابلة لإعادة الإنتاج من خلال تشغيل الأداة مرة أخرى\n"
    md += "- التركيز على الملفات الحرجة سيحقق أكبر تأثير إيجابي\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"💾 Markdown report saved: {output_path}")
