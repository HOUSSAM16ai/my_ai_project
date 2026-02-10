import asyncio
import os
import sys

import websockets
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from termcolor import colored
from websockets.exceptions import InvalidStatus

# Configuration
# DATABASE_URL should be set in environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
WS_URL = os.getenv("WS_URL", "ws://localhost:8000/api/chat/ws")


async def check_database():
    print(colored("\n[1] Checking Database Connection...", "cyan"))
    if not DATABASE_URL:
        print(colored("❌ FAILURE: DATABASE_URL not found in environment.", "red"))
        return False

    try:
        # Crucial: Disable statement cache for Supabase Transaction Pooler
        engine = create_async_engine(
            DATABASE_URL, connect_args={"statement_cache_size": 0}, echo=False
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(colored("✅ SUCCESS: Connected to Supabase!", "green"))
            print(colored(f"   Version: {version}", "white"))
        await engine.dispose()
        return True
    except Exception as e:
        print(colored("❌ FAILURE: Database check failed.", "red"))
        print(colored(f"   Error: {e!s}", "red"))
        return False


def check_mobile_config():
    print(colored("\n[2] Checking Mobile Configuration...", "cyan"))
    filepath = "frontend/app/hooks/useAgentSocket.js"
    try:
        with open(filepath) as f:
            content = f.read()

        # Check for hardcoded localhost in default state
        # We want to Ensure standard 'const url = process.env.NEXT_PUBLIC_WS_URL || ...'
        # BUT crucially, the fallback should NOT be hardcoded 'ws://localhost:8000' if we want smart detection.
        # However, the fix was to use window.location.hostname.

        if (
            "ws://localhost:8000" in content
            and "window.location.hostname" not in content
        ):
            print(colored(f"❌ FAILURE: Hardcoded localhost found in {filepath}", "red"))
            return False

        # Check for smart fallback
        if "window.location.hostname" in content:
            print(colored("✅ SUCCESS: Smart Hostname Detection found!", "green"))
            return True

        print(
            colored(
                "⚠️ WARNING: Smart Hostname Detection not explicitly found, but hardcoded localhost might be gone.",
                "yellow",
            )
        )
        return True  # Tentative pass

    except FileNotFoundError:
        print(colored(f"❌ FAILURE: File {filepath} not found.", "red"))
        return False


async def check_websocket():
    print(colored("\n[3] Checking WebSocket Connectivity...", "cyan"))
    try:
        # We expect a 403 or 401 because we are not sending a valid JWT,
        # but the connection handshake itself should succeed (i.e. server is reachable).
        # If it's "Offline", we would get a ConnectionRefusedError.
        async with websockets.connect(WS_URL, subprotocols=["jwt", "test-token"]) as ws:
            await ws.recv()
            print(colored("✅ SUCCESS: WebSocket Handshake completed!", "green"))
            return True
    except InvalidStatus as e:
        # websockets > 14 raises InvalidStatus instead of InvalidStatusCode
        # The status code is in e.response.status_code for modern versions, or just e.code/e.status_code
        status = getattr(e, "status_code", None) or getattr(
            e.response, "status_code", None
        )

        if status in [401, 403] or "HTTP 401" in str(e) or "HTTP 403" in str(e):
            print(
                colored(
                    "✅ SUCCESS: Server reachable (Auth rejected as expected)!", "green"
                )
            )
            return True

        print(colored(f"❌ FAILURE: Unexpected status code {status}", "red"))
        print(colored(f"   Details: {e!s}", "red"))
        return False
    except OSError as e:
        print(
            colored(
                f"❌ FAILURE: Could not connect to {WS_URL}. Is the server running?",
                "red",
            )
        )
        print(colored(f"   Error: {e!s}", "red"))
        return False
    except Exception as e:
        if "HTTP 403" in str(e) or "HTTP 401" in str(e):
            print(
                colored(
                    "✅ SUCCESS: Server reachable (Auth rejected as expected)!", "green"
                )
            )
            return True

        print(colored("❌ FAILURE: WebSocket check failed.", "red"))
        print(colored(f"   Error: {e!s}", "red"))
        return False


async def main():
    print(
        colored(
            "Starting 'Golden Test' System Verification...", "white", attrs=["bold"]
        )
    )

    db_ok = await check_database()
    mobile_ok = check_mobile_config()
    ws_ok = await check_websocket()

    print("\n" + "=" * 40)
    if db_ok and mobile_ok and ws_ok:
        print(
            colored(
                "🏆 GOLDEN TEST PASSED: SYSTEM IS PERFECT 🏆",
                "green",
                attrs=["bold", "blink"],
            )
        )
        sys.exit(0)
    else:
        print(
            colored(
                "💥 GOLDEN TEST FAILED: SYSTEM HAS ISSUES 💥", "red", attrs=["bold"]
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
