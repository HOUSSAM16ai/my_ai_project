
import asyncio
import sys
import os
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.core.settings.base import get_settings

async def verify_performance():
    print("🚀 Verifying 'Speed of Light' Performance...")

    # 1. Setup Connection
    settings = get_settings()
    # Use the actual file DB if available, otherwise memory
    db_url = "sqlite+aiosqlite:///./content.db" if os.path.exists("content.db") else "sqlite+aiosqlite:///:memory:"
    print(f"   Connecting to: {db_url}")

    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # 0. Ensure data exists (if in memory, we need to add some)
        if ":memory:" in db_url:
            await session.execute(text("CREATE TABLE IF NOT EXISTS content_items (id TEXT PRIMARY KEY, title TEXT, type TEXT, level TEXT, branch TEXT, subject TEXT, year INTEGER, lang TEXT, md_content TEXT, set_name TEXT, source_path TEXT, sha256 TEXT, updated_at TIMESTAMP)"))
            await session.execute(text("INSERT INTO content_items (id, title, level, branch, subject, year, set_name) VALUES ('perf-test', 'Performance Exercise', '3AS', 'Exp', 'Math', 2024, 'S1')"))
            await session.commit()

        # 1. Simulate Navigation (The "+" Menu)
        print("\n1. Simulating Navigation Menu (User Selection)...")
        t0 = time.perf_counter()

        # User selects Level -> Branch -> Subject -> Year -> Set
        # Finally, fetching the list of exercises
        result = await session.execute(text("SELECT id, title FROM content_items WHERE level='3AS' AND branch='Exp' AND subject='Math' AND year=2024 AND set_name='S1'"))
        exercises = result.fetchall()

        t1 = time.perf_counter()
        print(f"   ✅ Menu List Loaded in: {(t1-t0)*1000:.2f} ms")

        if not exercises and ":memory:" not in db_url:
             print("   ⚠️ No exercises found in real DB to test specific lookup. Using dummy if needed.")
             exercises = [('perf-test', 'Performance Exercise')]

        target_id = exercises[0][0] if exercises else 'perf-test'
        print(f"   🎯 Selected Target ID: {target_id}")

        # 2. Simulate "Instant Fetch" (Clicking the Title)
        print("\n2. Simulating Exercise Load (The 'Click')...")
        t_start = time.perf_counter()

        # This is the EXACT query used by /api/v1/content/{id}
        result = await session.execute(
            text("SELECT id, type, title, level, branch, subject, year, lang, md_content FROM content_items WHERE id = :id"),
            {"id": target_id}
        )
        content = result.fetchone()

        t_end = time.perf_counter()
        duration_ms = (t_end - t_start) * 1000

        print(f"   ⚡ Database Lookup Time: {duration_ms:.4f} ms")

        if duration_ms < 50:
            print("   ✅ RESULT: INSTANT (Under 50ms)")
        else:
            print("   ⚠️ RESULT: SLOW (Check Indexing)")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_performance())
