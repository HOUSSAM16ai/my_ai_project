
import asyncio
import json
import logging
import sys
from unittest.mock import MagicMock
from dataclasses import dataclass

# Setup paths
sys.path.append(".")

# Import the actual classes we modified
from app.services.overmind.executor import TaskExecutor
from app.services.chat.handlers.strategy_handlers import MissionComplexHandler
from app.core.domain.mission import Task, MissionEvent, MissionEventType

# Mock ToolResult to simulate what the tool returns
@dataclass
class ToolResult:
    ok: bool
    data: dict = None
    error: str = None

    def to_dict(self):
        return {"ok": self.ok, "data": self.data, "error": self.error}

# Mock a tool that "writes" a probability exercise
def mock_probability_tool(path, content):
    with open(path, "w") as f:
        f.write(content)
    return ToolResult(ok=True, data={"written": True, "path": path, "bytes": len(content)})

async def main():
    print("--- 🚀 محاكاة طلب: 'أعطني الإجابة النموذجية مع سلم التنقيط' ---")

    # 1. إعداد نص الحل فقط (من الملف الأصلي)
    solution_only_content = """# الحل النموذجي المفصل مع سلم التنقيط - احتمالات بكالوريا 2024

**مجموع الكرات:** $n = 11$.
**عدد السحوبات الممكنة:** $C_{11}^3 = \\frac{11 \\times 10 \\times 9}{3 \\times 2 \\times 1} = 165$. (0.25 ن)

### 1. حساب احتمال الحادثة A (من نفس اللون)
- الكرات البيضاء: 2 (لا يمكن سحب 3 لأن العدد أقل من 3).
- الكرات الحمراء: 4. $C_4^3 = 4$.
- الكرات الخضراء: 5. $C_5^3 = 10$.
- عدد الحالات الملائمة: $4 + 10 = 14$.
$$P(A) = \\frac{14}{165}$$
**(0.75 ن)**

### 2. حساب احتمال الحادثة B (الجداء فردي)
ليكون الجداء فردياً، يجب أن تكون كل الأرقام فردية.
الأرقام الفردية في الكيس:
- بيضاء: 1، 3 (عددها 2)
- حمراء: 1، 1، 3 (عددها 3)
- خضراء: 1، 1، 3 (عددها 3)
المجموع الكلي للكرات الفردية: $2 + 3 + 3 = 8$.
عدد الحالات الملائمة: $C_8^3 = \\frac{8 \\times 7 \\times 6}{6} = 56$.
$$P(B) = \\frac{56}{165}$$
**(0.75 ن)**

### 3. المتغير العشوائي X (عدد الكرات الزوجية)
الكرات الزوجية هي التي تحمل الأرقام: 0، 4.
- الأرقام الزوجية في الكيس:
  - حمراء: 0 (عددها 1)
  - خضراء: 0، 4 (عددها 2)
  - المجموع الكلي للكرات الزوجية: $1 + 2 = 3$.
- الكرات الفردية: 8.

**قيم المتغير العشوائي X:**
نسحب 3 كرات. عدد الكرات الزوجية يمكن أن يكون:
- 0 (كلها فردية)
- 1 (واحدة زوجية واثنتان فردية)
- 2 (اثنتان زوجية وواحدة فردية)
- 3 (كلها زوجية)
إذن قيم X هي: $\\{0, 1, 2, 3\\}$. **(0.5 ن)**

**قانون الاحتمال:**
- $P(X=0) = \\frac{C_8^3}{165} = \\frac{56}{165}$
- $P(X=1) = \\frac{C_3^1 \\times C_8^2}{165} = \\frac{3 \\times 28}{165} = \\frac{84}{165}$
- $P(X=2) = \\frac{C_3^2 \\times C_8^1}{165} = \\frac{3 \\times 8}{165} = \\frac{24}{165}$
- $P(X=3) = \\frac{C_3^3}{165} = \\frac{1}{165}$

التأكد: $56 + 84 + 24 + 1 = 165$. **(1.0 ن)**

**الأمل الرياضياتي E(X):**
$$E(X) = \\sum x_i P(X=x_i)$$
$$E(X) = 0(\\frac{56}{165}) + 1(\\frac{84}{165}) + 2(\\frac{24}{165}) + 3(\\frac{1}{165})$$
$$E(X) = \\frac{0 + 84 + 48 + 3}{165} = \\frac{135}{165} = \\frac{9}{11}$$
**(0.75 ن)**"""

    print("\n1. 🛠️  الوكيل يقوم بكتابة ملف الحل (solution_only.md)...")
    tool_result = mock_probability_tool("solution_only.md", solution_only_content)

    # 2. محاكاة عمل TaskExecutor
    print("2. ⚙️  TaskExecutor يعالج النتيجة...")
    executor_result = {
        "status": "success",
        "result_text": json.dumps(tool_result.to_dict()),
        "result_data": tool_result.to_dict(),
        "meta": {"tool": "create_solution"}
    }

    # 3. محاكاة عمل MissionComplexHandler
    print("3. 📝 MissionComplexHandler يقوم بتنسيق الرد النهائي...")

    mission_result_payload = {
        "results": [
            {
                "name": "توليد_الحل_النموذجي",
                "tool": "create_solution",
                "result": executor_result
            }
        ]
    }

    event = MissionEvent(
        mission_id=103,
        event_type=MissionEventType.MISSION_COMPLETED,
        payload_json={"result": mission_result_payload}
    )

    handler = MissionComplexHandler()
    formatted_msg = handler._format_event(event)

    print("\n" + "="*50)
    print("👇 النتيجة التي ستظهر للمستخدم في الشات 👇")
    print("="*50)
    print(formatted_msg)
    print("="*50)

    if "نص التمرين" not in formatted_msg and "سلم التنقيط" in formatted_msg:
        print("\n✅ نجاح: تم عرض الحل وسلم التنقيط فقط!")
    else:
        print("\n❌ فشل: النتيجة غير متوقعة.")

if __name__ == "__main__":
    asyncio.run(main())
