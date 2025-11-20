import time
import requests
import statistics
import threading
import json

# Basic performance smoke test script
# Assumes app is running on localhost:8000

BASE_URL = "http://localhost:8000"
HEALTH_URL = f"{BASE_URL}/health"


def test_latency(url, n=50):
    latencies = []
    errors = 0
    for _ in range(n):
        try:
            start = time.time()
            resp = requests.get(url)
            if resp.status_code == 200:
                latencies.append((time.time() - start) * 1000)
            else:
                errors += 1
        except Exception:
            errors += 1

    if not latencies:
        return {"error": "All requests failed"}

    return {
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "avg_ms": statistics.mean(latencies),
        "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)],
        "requests": n,
        "errors": errors,
    }


if __name__ == "__main__":
    print(f"Running Performance Smoke Test against {HEALTH_URL}")

    # Wait for service (manual run assumption or CI service)
    # In this environment, we need to start the app first or assume it's up.
    # Since we can't easily start bg process and query it in same script without complexity,
    # we will trust the `test_startup.py` for functionality and this script is for CI use.
    # However, we can simulate internal latency check if we import app directly.

    # For the sake of the report, we will output a placeholder if not running.
    try:
        res = test_latency(HEALTH_URL, n=20)
        print(json.dumps(res, indent=2))
        with open("reports/omega/perf_summary.md", "w") as f:
            f.write("# Performance Summary\n\n")
            f.write("## Health Endpoint Latency\n")
            f.write(f"```json\n{json.dumps(res, indent=2)}\n```\n")
    except Exception as e:
        print(f"Could not connect: {e}")
        with open("reports/omega/perf_summary.md", "w") as f:
            f.write("# Performance Summary\n\n")
            f.write("Could not run live performance test (Service not reachable).\n")
