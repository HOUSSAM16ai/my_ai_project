import os
import sys
import traceback

# Mimic the environment variable set by conftest (or lack thereof)
# Uncomment to test if manual override fixes it
# os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

print(f"Current DATABASE_URL: {os.environ.get('DATABASE_URL')}")

try:
    print("Attempting to import app.kernel...")
    from app import kernel
    print("Import successful!")
except Exception:
    traceback.print_exc()
