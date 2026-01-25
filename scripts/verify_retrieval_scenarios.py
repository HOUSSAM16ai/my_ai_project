import asyncio
import os
import ssl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Securely get DB URL
DATABASE_URL = os.environ.get("DATABASE_URL")

async def verify_scenarios():
    print("🚀 Starting Advanced Retrieval Verification (The Gauntlet)...")

    if not DATABASE_URL:
        print("❌ DATABASE_URL not set.")
        return

    # Setup Async Engine
    # Remove sslmode from URL as we handle it manually via context
    url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("?sslmode=require", "").replace("&sslmode=require", "")
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        url,
        echo=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "ssl": ssl_ctx
        }
    )

    try:
        async with engine.connect() as conn:
            print("\n🔍 SCENARIO 1: Strict Metadata Filtering (The Logic Gate)")
            # Simulates: "Give me 2024 Math Experimental Sciences exercises"
            # This is what the Search Engine does when it extracts entities from the prompt.
            stmt_strict = text("""
                SELECT id, title, year, branch
                FROM content_items
                WHERE year = 2024
                  AND subject = 'mathematics'
                  AND branch = 'experimental_sciences'
            """)
            result = await conn.execute(stmt_strict)
            rows = result.fetchall()

            target_id = 'bac-2024-exp-math-s1-ex1'
            found_strict = any(r.id == target_id for r in rows)

            if found_strict:
                print(f"✅ PASSED: Found {target_id} using strict filters.")
            else:
                print(f"❌ FAILED: Could not find {target_id} with strict filters.")

            print("\n🔍 SCENARIO 2: Graph/Vector Linkage (The Neural Path)")
            # Simulates: Semantic Search finds a Knowledge Node (via embedding),
            # and the system tries to resolve it to a Content Item.
            # We check if the Knowledge Nodes for this exercise have the 'content_id' set.
            node_name_query = "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية"
            stmt_graph = text("""
                SELECT id, name, metadata
                FROM knowledge_nodes
                WHERE name = :name
            """)
            result_graph = await conn.execute(stmt_graph, {"name": node_name_query})
            nodes = result_graph.fetchall()

            if not nodes:
                print(f"⚠️ WARNING: No knowledge nodes found for '{node_name_query}'. Semantic search might fail if embeddings rely on this exact name.")
            else:
                linked_nodes = 0
                for node in nodes:
                    meta = node.metadata
                    # Handle both dict and string formats of JSONB
                    if isinstance(meta, str):
                        import json
                        meta = json.loads(meta)

                    if meta.get("content_id") == target_id:
                        linked_nodes += 1
                        print(f"   - Node {node.id}: LINKED ✅")
                    else:
                         print(f"   - Node {node.id}: UNLINKED ❌ (Meta: {meta})")

                if linked_nodes == len(nodes):
                    print(f"✅ PASSED: All {len(nodes)} relevant Knowledge Nodes are linked to the content.")
                else:
                    print(f"❌ FAILED: Only {linked_nodes}/{len(nodes)} nodes are linked.")

            print("\n🔍 SCENARIO 3: Keyword Fallback (The Safety Net)")
            # Check content first
            stmt_check = text("SELECT plain_text FROM content_search WHERE content_id = :cid")
            res_check = await conn.execute(stmt_check, {"cid": target_id})
            row_check = res_check.fetchone()
            if row_check:
                text_content = row_check[0]
                print(f"   Content Length: {len(text_content)}")
                print(f"   Has '2024': {'2024' in text_content}")
                print(f"   Has 'احتمال': {'احتمال' in text_content}")
                print(f"   Has 'كرات': {'كرات' in text_content}")

            # Simulates: Search fails to find vectors, falls back to text search on the body.
            # "Probability" + "2024"
            stmt_keyword = text("""
                SELECT content_id
                FROM content_search
                WHERE plain_text LIKE '%2024%'
                  AND (plain_text LIKE '%احتمال%' OR plain_text LIKE '%كرات%')
                  AND content_id = :cid
            """)
            result_kw = await conn.execute(stmt_keyword, {"cid": target_id})
            if result_kw.fetchone():
                print(f"✅ PASSED: Content is indexed for keywords '2024' and 'Probability/Balls'.")
            else:
                print(f"❌ FAILED: Keywords not found in content_search. (Metadata allows filtering, but pure keyword search needs the year in text/title)")

    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_scenarios())
