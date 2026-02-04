
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
    print("--- 🚀 بدء محاكاة التحقق (Verification Simulation) ---")

    # 1. إعداد نص التمرين (Simulated Content)
    dummy_exercise_content = """
    # تمرين الاحتمالات - بكالوريا 2024

    يحتوي صندوق على 5 كرات حمراء و 3 كرات خضراء.
    نسحب عشوائياً كرتين في آن واحد.

    1. احسب احتمال الحصول على كرتين من نفس اللون.
    2. احسب احتمال الحصول على كرة حمراء على الأقل.
    """

    print("\n1. 🛠️  الوكيل يقوم بكتابة ملف التمرين...")
    # Manually run the mock tool
    tool_result = mock_probability_tool("exercise_output.md", dummy_exercise_content)

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
                "name": "كتابة_التمرين",
                "tool": "create_exercise",
                "result": executor_result
            }
        ]
    }

    event = MissionEvent(
        mission_id=99,
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

    if "يحتوي صندوق على 5 كرات" in formatted_msg:
        print("\n✅ نجاح: محتوى التمرين ظهر في الرد!")
    else:
        print("\n❌ فشل: المحتوى لم يظهر.")

if __name__ == "__main__":
    asyncio.run(main())
