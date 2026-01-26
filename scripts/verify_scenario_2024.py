import asyncio

from app.services.content.service import content_service


async def verify_scenario():
    print("--- 🔍 COMPLEX SCENARIO VERIFICATION 🔍 ---\n")
    print("Query: 'Bac Experimental Sciences, Math, Subject 1, Ex 1, Probabilities, 2024'")

    # We map the user's natural language request to these specific parameters:
    # Branch: Experimental Sciences -> 'experimental_sciences'
    # Subject: Mathematics -> 'mathematics'
    # Set: Subject 1 -> 'subject_1'
    # Year: 2024
    # Keyword: Probabilities -> 'الاحتمالات'

    # Note: 'q' acts as a text filter. If the text contains "الاحتمالات", it should match.
    # However, since the title is "Exercise 1", we might need to rely on body search.

    results = await content_service.search_content(
        q="الاحتمالات",  # Search for 'Probabilities' in text
        year=2024,
        subject="mathematics",
        branch="experimental_sciences",
        set_name="subject_1",
        limit=5,
    )

    if results:
        print(f"✅ SUCCESS: Found {len(results)} matching item(s).")
        for res in results:
            print(f"   - ID: {res['id']}")
            print(f"   - Title: {res['title']}")
            print(f"   - Branch: {res['branch']}")
            print(f"   - Set: {res['set']}")

            # Fetch content to verify text
            details = await content_service.get_content_raw(res["id"])
            if details:
                text = details.get("content", "")
                print(f"   - Content Length: {len(text)} chars")
                snippet = text[:200].replace("\n", " ")
                print(f"   - Snippet: {snippet}...")

                if "حتمال" in text or "probabilit" in text.lower():
                    print("   - ✅ Keyword 'Probabilities' verified in text.")
                else:
                    print("   - ⚠️ Keyword 'Probabilities' NOT found in text.")
    else:
        print("❌ FAILURE: No items found matching this specific combination.")

        # fallback check without text query to see if metadata matches at least
        print("\n   [DEBUG] Retrying without text query 'الاحتمالات'...")
        results_loose = await content_service.search_content(
            q="",
            year=2024,
            subject="mathematics",
            branch="experimental_sciences",
            set_name="subject_1",
            limit=5,
        )
        if results_loose:
            print(f"   ⚠️ Found {len(results_loose)} item(s) via metadata ONLY (Text mismatch?).")
            print(f"   - Title: {results_loose[0]['title']}")
        else:
            print("   ❌ Still no results. Metadata mismatch suspected.")


if __name__ == "__main__":
    asyncio.run(verify_scenario())
