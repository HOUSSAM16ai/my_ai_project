#!/bin/bash
# ======================================================================================
# Local CI Test Script - Run CI checks locally before pushing
# ======================================================================================
# This script mimics GitHub Actions checks locally to catch issues early
# Usage: ./scripts/ci/test-locally.sh
# ======================================================================================

set -e

echo "🚀 Running local CI checks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to run check
run_check() {
    local name="$1"
    local cmd="$2"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Running: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ $name: PASSED${NC}"
    else
        echo -e "${RED}❌ $name: FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# 1. Black formatting
run_check "Black Formatting" \
    "black --check --diff --color --line-length=100 app/ tests/"

# 2. Import sorting
run_check "Import Sorting (isort)" \
    "isort --check-only --diff --profile=black --line-length=100 app/ tests/"

# 3. Ruff linting
run_check "Ruff Linting" \
    "ruff check app/ tests/"

# 4. MyPy type checking (informational)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔬 Running: MyPy Type Checking (informational)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mypy app/ --ignore-missing-imports --show-error-codes --pretty || true
echo -e "${YELLOW}ℹ️  MyPy: INFORMATIONAL (doesn't affect CI)${NC}"

# 5. Security scan
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 Running: Security Scan (Bandit)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bandit -r app/ -c pyproject.toml > /tmp/bandit-output.txt || true
cat /tmp/bandit-output.txt | tail -20

# Extract high severity count
HIGH_COUNT=$(grep -o "High: [0-9]*" /tmp/bandit-output.txt | grep -o "[0-9]*" || echo "0")
if [ "$HIGH_COUNT" -gt 15 ]; then
    echo -e "${RED}❌ Security: FAILED (High severity: $HIGH_COUNT > 15)${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ Security: PASSED (High severity: $HIGH_COUNT ≤ 15)${NC}"
fi

# 6. Tests
run_check "Unit Tests" \
    "pytest -v --tb=short --timeout=60 --maxfail=5 --cov=app --cov-report=term"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED check(s) failed. Please fix before pushing.${NC}"
    echo ""
    echo "💡 Quick fixes:"
    echo "   - Black: black --line-length=100 app/ tests/"
    echo "   - isort: isort --profile=black --line-length=100 app/ tests/"
    echo "   - Ruff: ruff check --fix app/ tests/"
    echo ""
    exit 1
fi
