
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
    print("--- 🚀 محاكاة طلب: 'أعطني الأسئلة فقط بدون حل' ---")

    # 1. إعداد نص التمرين (الأسئلة فقط)
    # The agent would extract just this part based on the user's prompt
    questions_only_content = """# تمرين الاحتمالات بكالوريا 2024 (الأسئلة فقط)

## نص التمرين
يحتوي كيس على 11 كرة لا نفرق بينها باللمس، موزعة كالتالي:
- كرتان (2) بيضاوان تحملان الرقمين: 1، 3.
- أربع (4) كرات حمراء تحمل الأرقام: 0، 1، 1، 3.
- خمس (5) كرات خضراء تحمل الأرقام: 0، 1، 1، 3، 4.

نسحب عشوائياً وفي آن واحد 3 كرات من الكيس.

### الأسئلة
1. أحسب احتمال الحادثة A: "الكرات المسحوبة من نفس اللون".
2. أحسب احتمال الحادثة B: "جداء الأرقام التي تحملها الكرات المسحوبة عدد فردي".
3. ليكن المتغير العشوائي X الذي يرفق بكل سحب عدد الكرات التي تحمل رقماً زوجياً.
   - عين قيم المتغير العشوائي X.
   - عرف قانون الاحتمال للمتغير X وأحسب أمله الرياضياتي E(X)."""

    print("\n1. 🛠️  الوكيل يقوم بكتابة ملف الأسئلة فقط (questions_only.md)...")
    # Manually run the mock tool
    tool_result = mock_probability_tool("questions_only.md", questions_only_content)

    # 2. محاكاة عمل TaskExecutor
    print("2. ⚙️  TaskExecutor يعالج النتيجة...")
    executor_result = {
        "status": "success",
        "result_text": json.dumps(tool_result.to_dict()),
        "result_data": tool_result.to_dict(),
        "meta": {"tool": "create_exercise"}
    }

    # 3. محاكاة عمل MissionComplexHandler
    print("3. 📝 MissionComplexHandler يقوم بتنسيق الرد النهائي...")

    mission_result_payload = {
        "results": [
            {
                "name": "توليد_الأسئلة_فقط",
                "tool": "create_exercise",
                "result": executor_result
            }
        ]
    }

    event = MissionEvent(
        mission_id=102,
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

    if "الحل النموذجي" not in formatted_msg and "الأسئلة" in formatted_msg:
        print("\n✅ نجاح: تم عرض الأسئلة فقط واختفى الحل!")
    else:
        print("\n❌ فشل: النتيجة غير متوقعة.")

if __name__ == "__main__":
    asyncio.run(main())
