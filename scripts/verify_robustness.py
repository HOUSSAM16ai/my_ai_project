import asyncio
import os
import logging
import sys

# Setup Logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Import the tool
from app.services.chat.tools.content import search_content

TEST_QUERIES = [
    # 1. The Disaster Case (Fixed previously)
    "اعطني أسئلة امتحان مادة الرياضيات تمرين الاحتمالات الموضوع الاول التمرين الأول لسنة 2024 لشعبة العلوم التجريبية",

    # 2. Simple Direct
    "تمرين احتمالات 2024 علوم تجريبية",

    # 3. Conversational / Dialect
    "ممكن تشوفلي تمرين نتاع الاحتمالات لي جا في الباك تاع 2024 شعبة علوم؟",

    # 4. Content Specific (Balls/Colors)
    "تمرين الكرات والالوان باك 2024 رياضيات",

    # 5. Content Specific (Dice/Nard)
    "مسألة رمي حجر نرد بكالوريا 2024",

    # 6. Metadata Heavy
    "الموضوع الأول التمرين 1 رياضيات 2024",

    # 7. French Mixed
    "Exercice probabilité bac 2024 experimental sciences",

    # 8. Imperative Synonyms
    "هات تمرين الاحتمالات للعام الماضي",

    # 9. Typo Heavy
    "تمرين إحتمالات بكالوريا 2024 تجربية",

    # 10. Very Short
    "احتمالات 2024"
]

async def verify_robustness():
    print("\n🚀 Starting Robustness Verification (10 Scenarios)\n")

    passes = 0
    fails = 0

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"🔹 Scenario {i}: '{query}'")
        try:
            results = await search_content(q=query, limit=3)

            found = False
            for res in results:
                if res.get('id') == 'ex_1':
                    found = True
                    break

            if found:
                print(f"   ✅ PASS: Found 'ex_1'")
                passes += 1
            else:
                print(f"   ❌ FAIL: 'ex_1' not found. Results: {len(results)}")
                for r in results:
                    print(f"      - Found: {r.get('id')} ({r.get('title')})")

        except Exception as e:
            print(f"   ⚠️ ERROR: {e}")
            fails += 1

        print("-" * 40)

    print(f"\n🏁 Summary: {passes}/10 Passed")

if __name__ == "__main__":
    asyncio.run(verify_robustness())
