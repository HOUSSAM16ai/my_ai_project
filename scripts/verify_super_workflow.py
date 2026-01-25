import asyncio
import os
import logging
from app.core.gateway.simple_client import SimpleAIClient
from app.services.reasoning.workflow import SuperReasoningWorkflow
from app.core.db_schema import validate_schema_on_startup

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-super")

async def main():
    print("🧠 Verifying Super Reasoner Integration...")

    # 1. Ensure DB Schema (just in case)
    # await validate_schema_on_startup()

    # 2. Initialize Client
    api_key = os.environ.get("OPENROUTER_API_KEY")
    client = SimpleAIClient(api_key=api_key)

    # 3. Create Workflow
    workflow = SuperReasoningWorkflow(client=client, verbose=True)

    # 4. Run Query
    query = "حل تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية"
    print(f"❓ Query: {query}")

    try:
        result = await workflow.run(query=query)
        print("\n✅ Result from Super Reasoner:\n")
        print("="*60)
        print(result)
        print("="*60)
    except Exception as e:
        print(f"❌ Verification Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
