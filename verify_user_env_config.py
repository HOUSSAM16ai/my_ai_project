#!/usr/bin/env python3
"""Test comprehensive mode with user's actual .env configuration"""

import os
import sys

sys.path.insert(0, "/home/ubuntu/repos/my_ai_project")

os.environ["PLANNER_INDEX_FILE"] = "1"
os.environ["PLANNER_DEEP_INDEX_JSON"] = "1"
os.environ["PLANNER_DEEP_INDEX_MD"] = "1"
os.environ["PLANNER_COMPREHENSIVE_MODE"] = "1"

try:
    from app.overmind.planning.llm_planner import (
        COMPREHENSIVE_MODE,
        DEEP_INDEX_JSON_EN,
        DEEP_INDEX_MD_EN,
        INDEX_FILE_EN,
    )

    print("=== TESTING WITH USER'S ENV CONFIGURATION ===")
    print(f"PLANNER_INDEX_FILE env var: {os.environ.get('PLANNER_INDEX_FILE')}")
    print(f"PLANNER_DEEP_INDEX_JSON env var: {os.environ.get('PLANNER_DEEP_INDEX_JSON')}")
    print(f"PLANNER_DEEP_INDEX_MD env var: {os.environ.get('PLANNER_DEEP_INDEX_MD')}")
    print(f"PLANNER_COMPREHENSIVE_MODE env var: {os.environ.get('PLANNER_COMPREHENSIVE_MODE')}")
    print()
    print(f"COMPREHENSIVE_MODE: {COMPREHENSIVE_MODE}")
    print(f"INDEX_FILE_EN: {INDEX_FILE_EN}")
    print(f"DEEP_INDEX_JSON_EN: {DEEP_INDEX_JSON_EN}")
    print(f"DEEP_INDEX_MD_EN: {DEEP_INDEX_MD_EN}")
    print()

    if COMPREHENSIVE_MODE and not INDEX_FILE_EN and not DEEP_INDEX_JSON_EN and not DEEP_INDEX_MD_EN:
        print("✅ COMPREHENSIVE MODE WORKS WITH USER'S ENV!")
        print("✅ All fragmented file creation flags are properly disabled")
        sys.exit(0)
    else:
        print("❌ User's env configuration still causes fragmented files")
        print("❌ The hardcoded env flags override our conditional logic")
        sys.exit(1)

except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
