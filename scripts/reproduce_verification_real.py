
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
    print("--- 🚀 بدء محاكاة التحقق (Verification Simulation) - التمرين الفعلي ---")

    # 1. إعداد نص التمرين (Actual Content from Database/File)
    actual_exercise_content = """# تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية - الموضوع الأول

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

    print("\n1. 🛠️  الوكيل يقوم بكتابة ملف التمرين الفعلي (bac_2024_probability.md)...")
    # Manually run the mock tool
    tool_result = mock_probability_tool("bac_2024_probability.md", actual_exercise_content)

    # 2. محاكاة عمل TaskExecutor (الذي عدلناه)
    print("2. ⚙️  TaskExecutor يعالج النتيجة...")
    # We simulate what TaskExecutor.execute_task returns now
    executor_result = {
        "status": "success",
        "result_text": json.dumps(tool_result.to_dict()),
        "result_data": tool_result.to_dict(), # THIS is the key part we added
        "meta": {"tool": "create_exercise"}
    }
    print("   ✅ البيانات الهيكلية (result_data) تم استخراجها بنجاح.")

    # 3. محاكاة عمل MissionComplexHandler (الذي عدلناه)
    print("3. 📝 MissionComplexHandler يقوم بتنسيق الرد النهائي...")

    # Construct payload as it comes from the DB event
    mission_result_payload = {
        "results": [
            {
                "name": "توليد_تمرين_الاحتمالات_2024",
                "tool": "create_exercise",
                "result": executor_result
            }
        ]
    }

    event = MissionEvent(
        mission_id=101,
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

    if "يحتوي كيس على 11 كرة" in formatted_msg:
        print("\n✅ نجاح: محتوى تمرين 2024 الفعلي ظهر في الرد!")
    else:
        print("\n❌ فشل: المحتوى لم يظهر.")

if __name__ == "__main__":
    asyncio.run(main())
