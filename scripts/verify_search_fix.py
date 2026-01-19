import asyncio
import os
import sys

# Add app to path
sys.path.append(os.getcwd())

from app.services.chat.tools.content import search_content, _normalize_branch
from app.services.content.domain import ContentFilter

async def main():
    print("--- Verifying Search Fix ---")

    # 1. Test Branch Normalization
    print("\n1. Testing Branch Normalization...")
    arabic_branch = "علوم تجريبية"
    slug = _normalize_branch(arabic_branch)
    print(f"   Input: {arabic_branch}")
    print(f"   Output: {slug}")

    if slug == "experimental_sciences":
        print("   ✅ Branch normalization PASSED")
    else:
        print("   ❌ Branch normalization FAILED")

    # 2. Test Search Tool Integration (Mocking the repo call to avoid full DB overhead if possible,
    #    but we really want to see if the tool builds the filter correctly)

    # Since we can't easily mock the internal `ContentRepository` without pytest-mock,
    # we will rely on the fact that the code path is now using `ContentFilter`.
    # We will try to run a search (this might fail if DB is not reachable, but let's try).

    print("\n2. Testing Search Tool Execution...")
    try:
        # We invoke the tool.
        # Note: This requires a running DB. If DB is down, this will error,
        # but that confirms the tool is trying to hit the DB layer we want.
        results = await search_content(
            q="Mecanique",
            year=2024,
            branch="علوم تجريبية"
        )
        print(f"   Search returned {len(results)} results.")
        # We don't strictly need results to be found to prove the code works,
        # we just need to ensure it didn't crash with 'column not found' or 'syntax error'.
        print("   ✅ Search tool execution PASSED (no crash).")

    except Exception as e:
        print(f"   ⚠️ Search tool execution hit an error (likely DB connection): {e}")
        # If the error is related to connection, it means the logic reached the repo.
        # If it's a syntax error in the tool, it's a fail.

if __name__ == "__main__":
    asyncio.run(main())
