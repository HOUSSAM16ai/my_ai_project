import asyncio
import logging
import os

from app.core.gateway.simple_client import SimpleAIClient
from app.services.reasoning.workflow import SuperReasoningWorkflow

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-strict")


async def main():
    print("🧠 Verifying Strict Search & Reasoning...")

    # 1. Initialize Client
    api_key = os.environ.get("OPENROUTER_API_KEY")
    client = SimpleAIClient(api_key=api_key)

    # 2. Create Workflow
    workflow = SuperReasoningWorkflow(client=client, timeout=300, verbose=True)

    # 3. Run Query (Strict Arabic)
    query = "تمرين في مادة الرياضيات خاص بالاحتمالات في شعبة العلوم التجريبية بكالوريا 2024 الموضوع الاول التمرين الأول"
    print(f"❓ Query: {query}")

    try:
        result = await workflow.run(query=query)
        print("\n✅ Result from Super Reasoner:\n")
        print("=" * 60)
        print(result)
        print("=" * 60)

        # Simple string check for success
        res_str = str(result)
        if "14/165" in res_str or "56/165" in res_str or "11 كرة" in res_str:
            print("🎉 SUCCESS: The exercise was found and solved correctly.")
        else:
            print("⚠️ WARNING: The result might not contain the exact numbers. Check output.")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
