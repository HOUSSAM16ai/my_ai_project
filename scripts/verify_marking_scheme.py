import asyncio
import sys
from unittest.mock import MagicMock
from types import ModuleType

# Setup sys.path to ensure we are running from root
sys.path.append("/app")

# Mock heavy dependencies
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["dspy"] = MagicMock()
sys.modules["openai"] = MagicMock()
sys.modules["app.services.chat.orchestrator"] = MagicMock()
sys.modules["app.services.chat.tools.content"] = MagicMock()

# Now we can import the service
from app.services.chat.tools.retrieval.service import search_educational_content

async def main():
    print("--- Searching for Exercise 1 (Probability) - Questions Only ---")
    # Note: 'subject_1' matches the 'set: subject_1' in the content file
    result_ex1 = await search_educational_content(
        query="التمرين الأول الاحتمالات",
        year="2024",
        subject="Mathematics",
        branch="Experimental Sciences",
        exam_ref="Subject 1"
    )
    print("Result Length:", len(result_ex1))
    print("Result Preview (End of text):\n", result_ex1[-200:])

    # Assertions
    if "حل التمرين" in result_ex1 or "الحل" in result_ex1:
        print("\n[FAIL] Result contains 'Solution' section!")
    else:
        print("\n[PASS] Solution excluded.")

    if "المتغير العشوائي" in result_ex1:
        print("[PASS] Contains exercise content.")
    else:
        print("[FAIL] Missing exercise content.")

if __name__ == "__main__":
    asyncio.run(main())
