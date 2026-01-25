import asyncio
import logging
from app.services.search_engine.hybrid import hybrid_search
from app.core.logging import get_logger

# Mute noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

async def verify_super_search():
    queries = [
        "تمرين 1 رياضيات 2024 علوم تجريبية الموضوع 1",
        "احسب الاحتمال الشرطي",
        "What is the expected value of X?",
        "الكرات البيضاء والحمراء"
    ]

    print("\n🚀 Testing 'Super Hybrid Search' (Dense + Sparse + Rerank)...")

    for query in queries:
        print(f"\n🔎 Query: '{query}'")
        print("=" * 60)

        results = await hybrid_search(query, top_k=5)

        if not results:
            print("❌ No results found.")
            continue

        for i, res in enumerate(results):
            # Breakdown
            dense = res.get('dense_score', 0)
            sparse = res.get('norm_sparse', 0)
            hybrid = res.get('hybrid_score', 0)
            rerank = res.get('rerank_score', 0)

            print(f"{i+1}. [{res['label']}] {res['name']}")
            print(f"   🏆 Final Rerank Score: {rerank:.4f}")
            print(f"   📊 Breakdown: Dense({dense:.2f}) + Sparse({sparse:.2f}) -> Hybrid({hybrid:.2f})")
            print(f"   📄 Content: {res['content'][:100]}...")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(verify_super_search())
