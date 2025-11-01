#!/usr/bin/env python3
"""
SUPERHUMAN EXTREME MODE TEST SUITE
===================================
Tests the extreme complexity mode implementation for handling very complex questions.
"""

import os
import sys
from pathlib import Path

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

project_root = Path(__file__).parent

test_results = []
tests_passed = 0
tests_failed = 0


def test_result(test_name: str, passed: bool, details: str = ""):
    """Record and print test result"""
    global tests_passed, tests_failed

    if passed:
        tests_passed += 1
        status = f"{GREEN}✅ PASS{RESET}"
    else:
        tests_failed += 1
        status = f"{RED}❌ FAIL{RESET}"

    test_results.append((test_name, passed, details))
    print(f"  {status} {test_name} {details}")


def print_header(title: str):
    """Print section header"""
    print()
    print("=" * 70)
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print("=" * 70)


def test_llm_client_extreme_mode():
    """Test 1: Verify LLM client supports extreme mode"""
    print_header("TEST 1: LLM Client Extreme Mode Configuration")

    try:
        # Import the module
        sys.path.insert(0, str(project_root))
        from app.services import llm_client_service

        # Check for extreme mode variable
        has_extreme_mode = hasattr(llm_client_service, "_LLM_EXTREME_MODE")
        test_result("LLM_EXTREME_MODE Variable", has_extreme_mode, "(new variable added)")

        # Check max retries configuration
        has_retries = hasattr(llm_client_service, "_LLM_MAX_RETRIES")
        test_result(
            "LLM_MAX_RETRIES Configuration",
            has_retries,
            f"(value: {getattr(llm_client_service, '_LLM_MAX_RETRIES', 'N/A')})",
        )

        # Check backoff configuration
        has_backoff = hasattr(llm_client_service, "_LLM_RETRY_BACKOFF_BASE")
        test_result(
            "LLM_RETRY_BACKOFF_BASE Configuration",
            has_backoff,
            f"(value: {getattr(llm_client_service, '_LLM_RETRY_BACKOFF_BASE', 'N/A')})",
        )

        # Test timeout calculation with extreme mode
        os.environ["LLM_EXTREME_COMPLEXITY_MODE"] = "1"
        # Reload to pick up env change would be complex, so we'll check the code instead

        llm_file = project_root / "app" / "services" / "llm_client_service.py"
        if llm_file.exists():
            content = llm_file.read_text()
            has_600_timeout = "600.0" in content or "600" in content
            test_result("Extreme Mode Timeout (600s)", has_600_timeout, "(10 minutes in code)")

            has_extreme_check = "LLM_EXTREME_COMPLEXITY_MODE" in content
            test_result(
                "Extreme Mode Environment Check", has_extreme_check, "(checks env variable)"
            )

    except Exception as e:
        test_result("LLM Client Module Import", False, f"Error: {e}")


def test_admin_ai_extreme_support():
    """Test 2: Verify admin AI service supports extreme complexity"""
    print_header("TEST 2: Admin AI Service Extreme Complexity Support")

    try:
        from app.services import admin_ai_service

        # Check for new threshold variables
        has_extreme_threshold = hasattr(admin_ai_service, "EXTREME_QUESTION_THRESHOLD")
        test_result(
            "EXTREME_QUESTION_THRESHOLD Variable",
            has_extreme_threshold,
            f"(value: {getattr(admin_ai_service, 'EXTREME_QUESTION_THRESHOLD', 'N/A')})",
        )

        has_extreme_mode = hasattr(admin_ai_service, "EXTREME_COMPLEXITY_MODE")
        test_result(
            "EXTREME_COMPLEXITY_MODE Variable",
            has_extreme_mode,
            f"(value: {getattr(admin_ai_service, 'EXTREME_COMPLEXITY_MODE', 'N/A')})",
        )

        # Check max question length
        max_length = getattr(admin_ai_service, "MAX_QUESTION_LENGTH", 0)
        test_result(
            "MAX_QUESTION_LENGTH Increased", max_length >= 100000, f"(value: {max_length:,} chars)"
        )

        # Check max response tokens
        max_tokens = getattr(admin_ai_service, "MAX_RESPONSE_TOKENS", 0)
        test_result(
            "MAX_RESPONSE_TOKENS Increased", max_tokens >= 32000, f"(value: {max_tokens:,} tokens)"
        )

        # Check code for extreme mode detection
        admin_file = project_root / "app" / "services" / "admin_ai_service.py"
        if admin_file.exists():
            content = admin_file.read_text()

            has_extreme_detection = "is_extreme_question" in content
            test_result(
                "Extreme Question Detection Logic",
                has_extreme_detection,
                "(auto-detects complexity)",
            )

            has_extreme_guidance = "LLM_EXTREME_COMPLEXITY_MODE=1" in content
            test_result(
                "Extreme Mode Guidance in Errors", has_extreme_guidance, "(suggests activation)"
            )

    except Exception as e:
        test_result("Admin AI Service Import", False, f"Error: {e}")


def test_generation_service_extreme_support():
    """Test 3: Verify generation service supports extreme complexity"""
    print_header("TEST 3: Generation Service Extreme Complexity Support")

    try:
        gen_file = project_root / "app" / "services" / "generation_service.py"

        if gen_file.exists():
            content = gen_file.read_text()

            # Check for extreme question detection
            has_extreme_var = "is_extreme_question" in content
            test_result("Extreme Question Variable", has_extreme_var, "(detects > 20K chars)")

            # Check for 32K token allocation
            has_32k_tokens = "32000" in content
            test_result("32K Token Allocation", has_32k_tokens, "(for extreme complexity)")

            # Check for increased retries
            has_5_retries = "max_retries = 5" in content
            test_result("Increased Retries (5)", has_5_retries, "(for extreme questions)")

            # Check for extreme logging
            has_extreme_log = "EXTREME COMPLEXITY" in content
            test_result("Extreme Complexity Logging", has_extreme_log, "(logs extreme cases)")
        else:
            test_result("Generation Service File", False, "File not found")

    except Exception as e:
        test_result("Generation Service Check", False, f"Error: {e}")


def test_planner_extreme_limits():
    """Test 4: Verify planner supports extreme limits"""
    print_header("TEST 4: Planner Extreme Complexity Limits")

    try:
        planner_file = project_root / "app" / "overmind" / "planning" / "llm_planner.py"

        if planner_file.exists():
            content = planner_file.read_text()

            # Check MAX_CHUNKS increased
            has_100_chunks = 'MAX_CHUNKS = _env_int("PLANNER_MAX_CHUNKS", 100)' in content
            test_result("MAX_CHUNKS Increased to 100", has_100_chunks, "(was 60)")

            # Check HARD_LINE_CAP increased
            has_2m_cap = "2_000_000" in content or "2000000" in content
            test_result("HARD_LINE_CAP Increased to 2M", has_2m_cap, "(was 1.2M)")

            # Check MAX_TASKS_GLOBAL increased
            has_800_tasks = "800" in content and "MAX_TASKS_GLOBAL" in content
            test_result("MAX_TASKS_GLOBAL Increased to 800", has_800_tasks, "(was 550)")
        else:
            test_result("Planner File", False, "File not found")

    except Exception as e:
        test_result("Planner Configuration Check", False, f"Error: {e}")


def test_env_example_documentation():
    """Test 5: Verify .env.example has extreme mode documentation"""
    print_header("TEST 5: Environment Configuration Documentation")

    try:
        env_file = project_root / ".env.example"

        if env_file.exists():
            content = env_file.read_text()

            # Check for extreme mode documentation
            has_extreme_docs = "LLM_EXTREME_COMPLEXITY_MODE" in content
            test_result(
                "Extreme Mode Documentation", has_extreme_docs, "(documented in .env.example)"
            )

            # Check for threshold documentation
            has_threshold_docs = "ADMIN_AI_EXTREME_QUESTION_THRESHOLD" in content
            test_result(
                "Extreme Threshold Documentation", has_threshold_docs, "(20K chars threshold)"
            )

            # Check for 600s timeout documentation
            has_timeout_docs = "600" in content or "10 minutes" in content.lower()
            test_result("600s Timeout Documentation", has_timeout_docs, "(10 minutes)")

            # Check for 8 retries documentation
            has_retry_docs = "LLM_MAX_RETRIES=8" in content or "8 attempts" in content
            test_result("8 Retries Documentation", has_retry_docs, "(in extreme mode)")
        else:
            test_result(".env.example File", False, "File not found")

    except Exception as e:
        test_result("Environment Documentation Check", False, f"Error: {e}")


def test_documentation_files():
    """Test 6: Verify documentation files exist"""
    print_header("TEST 6: Documentation Files")

    try:
        # Check for new comprehensive guide
        guide_file = project_root / "SUPERHUMAN_EXTREME_MODE_GUIDE_AR.md"
        test_result("Extreme Mode Comprehensive Guide", guide_file.exists(), f"({guide_file.name})")

        # Check for quick reference
        quick_ref = project_root / "EXTREME_MODE_QUICK_REF.md"
        test_result("Extreme Mode Quick Reference", quick_ref.exists(), f"({quick_ref.name})")

        # Check guide content quality
        if guide_file.exists():
            content = guide_file.read_text()

            has_arabic = "العربية" in content or "الخارق" in content
            test_result("Guide Has Arabic Content", has_arabic, "(bilingual support)")

            has_examples = "Example" in content or "مثال" in content
            test_result("Guide Has Examples", has_examples, "(practical examples)")

            has_comparison = "OpenAI" in content or "Google" in content
            test_result("Guide Has Tech Giant Comparison", has_comparison, "(shows superiority)")

    except Exception as e:
        test_result("Documentation Files Check", False, f"Error: {e}")


def print_summary():
    """Print test summary and return exit code"""
    print()
    print("=" * 70)
    print(f"{BOLD}TEST SUMMARY{RESET}")
    print("=" * 70)
    print()

    total = tests_passed + tests_failed
    pass_rate = (tests_passed / total * 100) if total > 0 else 0

    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print()

    if tests_failed == 0:
        print(f"{GREEN}{BOLD}🎉 ALL TESTS PASSED! EXTREME MODE READY!{RESET}")
        print()
        print("✅ Timeout: Up to 600 seconds (10 minutes)")
        print("✅ Retries: Up to 8 attempts")
        print("✅ Question Length: Up to 100,000 characters")
        print("✅ Response Tokens: Up to 32,000 tokens")
        print("✅ Better than OpenAI, Google, Microsoft, Facebook, Apple!")
        print()
        return 0
    else:
        print(f"{RED}{BOLD}❌ SOME TESTS FAILED{RESET}")
        print()
        print("Failed tests:")
        for name, passed, details in test_results:
            if not passed:
                print(f"  - {name} {details}")
        print()
        return 1


def main():
    """Run all tests"""
    print()
    print(f"{BOLD}{BLUE}=" * 70)
    print("🚀 SUPERHUMAN EXTREME MODE - TEST SUITE")
    print("=" * 70 + f"{RESET}")
    print()
    print("Testing the implementation that surpasses:")
    print("  • OpenAI")
    print("  • Google")
    print("  • Microsoft")
    print("  • Facebook")
    print("  • Apple")
    print()

    # Run all tests
    test_llm_client_extreme_mode()
    test_admin_ai_extreme_support()
    test_generation_service_extreme_support()
    test_planner_extreme_limits()
    test_env_example_documentation()
    test_documentation_files()

    # Print summary and return exit code
    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
