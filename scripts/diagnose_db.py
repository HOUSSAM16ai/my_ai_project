import asyncio
import os
import ssl

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# User provided DB URL (Expects env var or interactive input)
DATABASE_URL = os.environ.get("DATABASE_URL")


async def diagnose():
    print("🔌 Connecting to DB...")

    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable is not set.")
        return

    # Ensure async driver
    url = (
        DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        .replace("?sslmode=require", "")
        .replace("&sslmode=require", "")
    )

    # SSL Context for asyncpg
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        url,
        echo=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "ssl": ssl_ctx,
        },
    )

    try:
        async with engine.connect() as conn:
            print("✅ Connected.")

            # Check for the specific exercise by name
            print("🔍 Searching for '2024' in knowledge_nodes...")

            # We search for name containing 2024 or content containing 2024
            # We assume the table is knowledge_nodes as per schema

            stmt = text("""
                SELECT id, name, label, content, metadata
                FROM knowledge_nodes
                WHERE name LIKE '%2024%' OR content LIKE '%2024%'
                LIMIT 10
            """)

            result = await conn.execute(stmt)
            rows = result.fetchall()

            if not rows:
                print("❌ No nodes found matching '2024'.")
            else:
                print(f"✅ Found {len(rows)} nodes:")
                for row in rows:
                    print("--------------------------------------------------")
                    print(f"ID: {row.id}")
                    print(f"Name: {row.name}")
                    print(f"Label: {row.label}")
                    print(f"Metadata: {row.metadata}")
                    print(f"Content Preview: {row.content[:100]}...")

            # Also check specifically for "Experimental Sciences" (علوم تجريبية)
            print("\n🔍 Searching for 'علوم تجريبية'...")
            stmt_sci = text("""
                SELECT id, name
                FROM knowledge_nodes
                WHERE name LIKE '%علوم تجريبية%' OR content LIKE '%علوم تجريبية%'
                LIMIT 5
            """)
            result_sci = await conn.execute(stmt_sci)
            rows_sci = result_sci.fetchall()
            if not rows_sci:
                print("❌ No nodes found matching 'علوم تجريبية'.")
            else:
                print(f"✅ Found {len(rows_sci)} nodes for 'Experimental Sciences'.")

            # Check content_items table
            print("\n🔍 Checking content_items table for 2024...")
            try:
                stmt_content = text("""
                    SELECT id, title, year, subject, branch, set_name
                    FROM content_items
                    WHERE year = 2024 OR title LIKE '%2024%'
                    LIMIT 5
                """)
                result_content = await conn.execute(stmt_content)
                rows_content = result_content.fetchall()
                if not rows_content:
                    print("❌ No content_items found for 2024.")
                else:
                    print(f"✅ Found {len(rows_content)} content_items for 2024:")
                    for row in rows_content:
                        print(f"   - {row}")
            except Exception as e:
                print(f"⚠️ Could not query content_items: {e}")

            # Check content_search table
            print("\n🔍 Checking content_search table...")
            try:
                stmt_search = text("""
                    SELECT content_id, substring(plain_text, 1, 50) as snippet
                    FROM content_search
                    WHERE content_id = 'bac-2024-exp-math-s1-ex1'
                """)
                result_search = await conn.execute(stmt_search)
                rows_search = result_search.fetchall()
                if not rows_search:
                    print(
                        "❌ No content_search entry for 'bac-2024-exp-math-s1-ex1'. Keyword search will fail on body text."
                    )
                else:
                    print(f"✅ Found content_search entry: {rows_search[0]}")
            except Exception as e:
                print(f"⚠️ Could not query content_search: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(diagnose())
