import asyncio
import sys
from unittest.mock import MagicMock

# Setup sys.path to ensure we are running from root
sys.path.append("/app")

# Mock heavy dependencies AGAIN to avoid loading them in this script
# Use sys.modules to mock
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["dspy"] = MagicMock()
sys.modules["openai"] = MagicMock()

# Import directly using Python's import system, assuming packages are valid
# We need to bypass the 'app.services.chat' import chain which loads heavy stuff.
# The previous attempt failed because 'app.services.chat.tools' was not recognized as a package
# because I was mocking it *incorrectly* or it was still trying to load the real one.

# Let's try to mock the *modules* that cause the import chain, rather than the packages themselves.
# The problematic modules are likely:
# app.services.chat.orchestrator
# app.services.chat.tools.content
# app.services.chat.agents...

sys.modules["app.services.chat.orchestrator"] = MagicMock()
sys.modules["app.services.chat.tools.content"] = MagicMock()

# Now we can import the service
from app.services.chat.tools.retrieval.service import search_educational_content


async def main():
    print("--- Searching for Exercise 1 (Probability) ---")
    result_ex1 = await search_educational_content(
        query="التمرين الأول الاحتمالات",
        year="2024",
        subject="Mathematics",
        branch="Experimental Sciences",
        exam_ref="Subject 1",
    )
    print("Result Ex 1 Length:", len(result_ex1))
    print("Result Ex 1 Preview:\n", result_ex1[:200])

    # Assertions for Ex 1
    if "التمرين الثاني" in result_ex1:
        print("\n[FAIL] Exercise 1 result contains Exercise 2 content!")
    else:
        print("\n[PASS] Exercise 2 excluded from Exercise 1 result.")

    print("\n--- Searching for Exercise 2 (Complex Numbers) ---")
    result_ex2 = await search_educational_content(
        query="Exercise 2 Complex Numbers",
        year="2024",
        subject="Mathematics",
        branch="Experimental Sciences",
        exam_ref="Subject 1",
    )
    print("Result Ex 2 Length:", len(result_ex2))
    print("Result Ex 2 Preview:\n", result_ex2[:200])

    # Assertions for Ex 2
    if "التمرين الأول" in result_ex2:
        print("\n[FAIL] Exercise 2 result contains Exercise 1 content!")
    else:
        print("\n[PASS] Exercise 1 excluded from Exercise 2 result.")

    if "وسوم بحث مقترحة" in result_ex2:
        print("[FAIL] Result contains metadata tags section!")
    else:
        print("[PASS] Metadata tags section excluded.")


if __name__ == "__main__":
    asyncio.run(main())
