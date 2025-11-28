import sys
import httpx
import time
import asyncio

async def verify_migration(base_url="http://localhost:8000"):
    print(f"Verifying migration against {base_url}...")
    errors = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. Check Root
        try:
            resp = await client.get(f"{base_url}/")
            if resp.status_code != 200:
                errors.append(f"Root / returned {resp.status_code}")
            elif "<!doctype html>" not in resp.text.lower() and "<html" not in resp.text.lower():
                errors.append("Root / does not appear to be HTML")
            else:
                print("✅ Root / is serving HTML")
        except Exception as e:
            errors.append(f"Root / connection failed: {e}")

        # 2. Check Static Assets
        assets = [
            "/css/superhuman-ui.css",
            "/js/script.js",
            "/js/superhuman-framework.js"
        ]
        for asset in assets:
            try:
                resp = await client.get(f"{base_url}{asset}")
                if resp.status_code != 200:
                    errors.append(f"Asset {asset} returned {resp.status_code}")
                elif int(resp.headers.get("content-length", 0)) == 0 and len(resp.content) == 0:
                    errors.append(f"Asset {asset} is empty")
                else:
                    print(f"✅ Asset {asset} is accessible")
            except Exception as e:
                errors.append(f"Asset {asset} connection failed: {e}")

        # 3. Check API Endpoint (Login)
        try:
            # We expect 422 Unprocessable Entity because we send empty body,
            # OR 200 if it handles it gracefully, but definitely NOT 404.
            resp = await client.post(f"{base_url}/api/security/login", json={})
            if resp.status_code == 404:
                 errors.append("API endpoint /api/security/login returned 404 (Not Found)")
            else:
                 print(f"✅ API /api/security/login is reachable (Status: {resp.status_code})")
        except Exception as e:
            errors.append(f"API /api/security/login connection failed: {e}")

    if errors:
        print("\n❌ Verification FAILED with errors:")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\n✅ All Checks Passed! Migration Verified.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(verify_migration())
    except ImportError:
        # Fallback for sync if asyncio/httpx fails (unlikely)
        import requests
        # ... sync impl if needed, but we stick to async as httpx is installed
        pass
