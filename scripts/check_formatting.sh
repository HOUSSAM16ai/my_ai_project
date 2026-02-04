#!/bin/bash
# ======================================================================================
# CHECK CODE FORMATTING - SUPERHUMAN EDITION 🏆
# ======================================================================================
# This script checks if code matches Black and isort standards WITHOUT modifying files
# Usage: ./scripts/check_formatting.sh
#
# Features:
# ✅ Checks Black formatting (line-length: 100)
# ✅ Checks import sorting (isort)
# ✅ Clear pass/fail indicators
# ✅ Helpful fix suggestions
# ✅ CI/CD friendly exit codes
# ======================================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${PURPLE}  🔍 CODE FORMATTING CHECK - SUPERHUMAN EDITION${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Must be run from project root (where pyproject.toml is located)${NC}"
    exit 1
fi

# Install formatting tools if needed
echo -e "${CYAN}📦 Checking formatting tools...${NC}"
pip install black isort --quiet --disable-pip-version-check

echo ""
echo -e "${CYAN}🔍 Checking Black formatting...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BLACK_PASSED=true
if black --check --diff --color --line-length=100 app/ tests/ 2>&1; then
    echo -e "${GREEN}✅ Black formatting: PASSED${NC}"
else
    echo ""
    echo -e "${RED}❌ Black formatting: FAILED${NC}"
    echo -e "${YELLOW}💡 Fix: Run ./scripts/format_code.sh${NC}"
    BLACK_PASSED=false
fi

echo ""
echo -e "${CYAN}🔍 Checking import sorting...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ISORT_PASSED=true
if isort --check-only --diff --profile=black --line-length=100 app/ tests/ 2>&1; then
    echo -e "${GREEN}✅ Import sorting: PASSED${NC}"
else
    echo ""
    echo -e "${RED}❌ Import sorting: FAILED${NC}"
    echo -e "${YELLOW}💡 Fix: Run ./scripts/format_code.sh${NC}"
    ISORT_PASSED=false
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"

if [ "$BLACK_PASSED" = true ] && [ "$ISORT_PASSED" = true ]; then
    echo -e "${GREEN}  ✅ ALL FORMATTING CHECKS PASSED!${NC}"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${CYAN}📊 Results:${NC}"
    echo -e "  ${GREEN}✓${NC} Black formatting: Compliant (line-length: 100)"
    echo -e "  ${GREEN}✓${NC} Import sorting: Compliant (isort + black profile)"
    echo ""
    echo -e "${PURPLE}🏆 Code quality: SUPERHUMAN${NC}"
    echo -e "${CYAN}🚀 Ready for CI/CD!${NC}"
    echo "════════════════════════════════════════════════════════════════════════════════"
    exit 0
else
    echo -e "${RED}  ❌ FORMATTING CHECKS FAILED${NC}"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${CYAN}📊 Results:${NC}"
    if [ "$BLACK_PASSED" = false ]; then
        echo -e "  ${RED}✗${NC} Black formatting: Failed"
    else
        echo -e "  ${GREEN}✓${NC} Black formatting: Passed"
    fi
    if [ "$ISORT_PASSED" = false ]; then
        echo -e "  ${RED}✗${NC} Import sorting: Failed"
    else
        echo -e "  ${GREEN}✓${NC} Import sorting: Passed"
    fi
    echo ""
    echo -e "${YELLOW}🔧 Quick fix:${NC}"
    echo -e "  ${CYAN}./scripts/format_code.sh${NC}"
    echo ""
    echo -e "${YELLOW}💡 Or fix manually:${NC}"
    if [ "$BLACK_PASSED" = false ]; then
        echo -e "  ${CYAN}black --line-length=100 app/ tests/${NC}"
    fi
    if [ "$ISORT_PASSED" = false ]; then
        echo -e "  ${CYAN}isort --profile=black --line-length=100 app/ tests/${NC}"
    fi
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    exit 1
fi
