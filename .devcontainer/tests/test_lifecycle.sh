#!/usr/bin/env bash
###############################################################################
# test_lifecycle.sh - Lifecycle System Test Suite
#
# مجموعة اختبارات نظام دورة الحياة
# Lifecycle System Test Suite
#
# الاستخدام (Usage):
#   bash .devcontainer/tests/test_lifecycle.sh
#
# الإصدار (Version): 1.0.0
# التاريخ (Date): 2025-12-31
###############################################################################

set -Eeuo pipefail

# ==============================================================================
# TEST FRAMEWORK (إطار الاختبار)
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LIB_DIR="$SCRIPT_DIR/../lib"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Test functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$expected" = "$actual" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} $message"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} $message"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        return 1
    fi
}

assert_true() {
    local condition="$1"
    local message="${2:-}"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if eval "$condition"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} $message"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} $message"
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-File should exist: $file}"
    
    assert_true "[ -f '$file' ]" "$message"
}

assert_command_exists() {
    local command="$1"
    local message="${2:-Command should exist: $command}"
    
    assert_true "command -v '$command' >/dev/null 2>&1" "$message"
}

# ==============================================================================
# TEST SUITES (مجموعات الاختبار)
# ==============================================================================

test_suite_core_library() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Test Suite: Core Library"
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Test: Library file exists
    assert_file_exists "$LIB_DIR/lifecycle_core.sh" "Core library file exists"
    
    # Test: Library can be sourced
    if source "$LIB_DIR/lifecycle_core.sh" 2>/dev/null; then
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} Core library can be sourced"
    else
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} Core library cannot be sourced"
        return 1
    fi
    
    # Test: Functions are exported
    assert_command_exists "lifecycle_log" "lifecycle_log function exists"
    assert_command_exists "lifecycle_set_state" "lifecycle_set_state function exists"
    assert_command_exists "lifecycle_check_port" "lifecycle_check_port function exists"
}

test_suite_state_management() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Test Suite: State Management"
    echo "═══════════════════════════════════════════════════════════════════"
    
    source "$LIB_DIR/lifecycle_core.sh"
    
    # Test: Set and get state
    lifecycle_set_state "test_state" "test_value"
    local value
    value=$(lifecycle_get_state "test_state")
    assert_equals "test_value" "$value" "State can be set and retrieved"
    
    # Test: Check state exists
    assert_true "lifecycle_has_state 'test_state'" "State existence check works"
    
    # Test: Clear state
    lifecycle_clear_state "test_state"
    assert_true "! lifecycle_has_state 'test_state'" "State can be cleared"
}

test_suite_locking() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Test Suite: Locking Mechanism"
    echo "═══════════════════════════════════════════════════════════════════"
    
    source "$LIB_DIR/lifecycle_core.sh"
    
    # Test: Acquire lock
    if lifecycle_acquire_lock "test_lock" 5; then
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} Lock can be acquired"
    else
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} Lock cannot be acquired"
    fi
    
    # Test: Release lock
    lifecycle_release_lock "test_lock"
    assert_true "! [ -f '.devcontainer/locks/test_lock.lock' ]" "Lock can be released"
}

test_suite_health_checks() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Test Suite: Health Checks"
    echo "═══════════════════════════════════════════════════════════════════"
    
    source "$LIB_DIR/lifecycle_core.sh"
    
    # Test: Port check (should fail for unused port)
    if lifecycle_check_port 99999; then
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} Port check should fail for unused port"
    else
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} Port check correctly fails for unused port"
    fi
    
    # Test: HTTP check (should fail for non-existent endpoint)
    if lifecycle_check_http "http://localhost:99999/nonexistent" 200; then
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} HTTP check should fail for non-existent endpoint"
    else
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} HTTP check correctly fails for non-existent endpoint"
    fi
}

test_suite_scripts() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Test Suite: Lifecycle Scripts"
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Test: Scripts exist
    assert_file_exists "$SCRIPT_DIR/../on-create.sh" "on-create.sh exists"
    assert_file_exists "$SCRIPT_DIR/../on-start.sh" "on-start.sh exists"
    assert_file_exists "$SCRIPT_DIR/../on-attach.sh" "on-attach.sh exists"
    assert_file_exists "$SCRIPT_DIR/../supervisor.sh" "supervisor.sh exists"
    
    # Test: Scripts are executable
    assert_true "[ -x '$SCRIPT_DIR/../on-create.sh' ]" "on-create.sh is executable"
    assert_true "[ -x '$SCRIPT_DIR/../on-start.sh' ]" "on-start.sh is executable"
    assert_true "[ -x '$SCRIPT_DIR/../on-attach.sh' ]" "on-attach.sh is executable"
    assert_true "[ -x '$SCRIPT_DIR/../supervisor.sh' ]" "supervisor.sh is executable"
    
    # Test: Scripts have proper shebang
    assert_true "head -1 '$SCRIPT_DIR/../on-create.sh' | grep -q '^#!/usr/bin/env bash'" "on-create.sh has proper shebang"
}

test_suite_utilities() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Test Suite: Utility Scripts"
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Test: Utility scripts exist
    assert_file_exists "$SCRIPT_DIR/../healthcheck.sh" "healthcheck.sh exists"
    assert_file_exists "$SCRIPT_DIR/../diagnostics.sh" "diagnostics.sh exists"
    
    # Test: Utilities are executable
    assert_true "[ -x '$SCRIPT_DIR/../healthcheck.sh' ]" "healthcheck.sh is executable"
    assert_true "[ -x '$SCRIPT_DIR/../diagnostics.sh' ]" "diagnostics.sh is executable"
}

# ==============================================================================
# MAIN EXECUTION (التنفيذ الرئيسي)
# ==============================================================================

main() {
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  CogniForge Lifecycle Test Suite"
    echo "  مجموعة اختبارات دورة حياة CogniForge"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Started: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Run test suites
    test_suite_core_library
    test_suite_state_management
    test_suite_locking
    test_suite_health_checks
    test_suite_scripts
    test_suite_utilities
    
    # Print summary
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Test Summary"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Total:  $TESTS_RUN"
    echo -e "  Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "  Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}✗ Some tests failed${NC}"
        exit 1
    fi
}

# Create tests directory if it doesn't exist
mkdir -p "$SCRIPT_DIR"

# Run main function
main
