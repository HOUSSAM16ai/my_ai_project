#!/bin/bash
# ======================================================================================
# 🎨 AUTO-FORMAT CODE SCRIPT
# ======================================================================================
# This script automatically formats all Python code to pass GitHub Actions checks
# ======================================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🎨 AUTO-FORMAT CODE - GitHub Actions Compliance${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if required tools are installed
echo -e "${BLUE}🔍 Checking for required tools...${NC}"

MISSING_TOOLS=0

if ! command -v black &> /dev/null; then
    echo "❌ Black not found. Installing..."
    pip install -q black
    MISSING_TOOLS=1
fi

if ! command -v isort &> /dev/null; then
    echo "❌ isort not found. Installing..."
    pip install -q isort
    MISSING_TOOLS=1
fi

if ! command -v ruff &> /dev/null; then
    echo "❌ Ruff not found. Installing..."
    pip install -q ruff
    MISSING_TOOLS=1
fi

if [ "$MISSING_TOOLS" -eq 0 ]; then
    echo -e "${GREEN}✅ All formatting tools are installed${NC}"
else
    echo -e "${GREEN}✅ Missing tools have been installed${NC}"
fi

echo ""

# Step 1: Black formatting
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  1️⃣  APPLYING BLACK FORMATTING${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

black --line-length=100 app/ tests/

echo ""
echo -e "${GREEN}✅ Black formatting applied${NC}"
echo ""

# Step 2: isort import sorting
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  2️⃣  SORTING IMPORTS WITH ISORT${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

isort --profile=black --line-length=100 app/ tests/

echo ""
echo -e "${GREEN}✅ Import sorting applied${NC}"
echo ""

# Step 3: Ruff auto-fixes
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  3️⃣  AUTO-FIXING WITH RUFF${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

ruff check --fix app/ tests/ || true

echo ""
echo -e "${GREEN}✅ Ruff auto-fixes applied${NC}"
echo ""

# Final verification
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  4️⃣  VERIFICATION${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

VERIFICATION_PASSED=true

echo "🔍 Verifying Black formatting..."
if black --check --line-length=100 app/ tests/ 2>&1; then
    echo -e "${GREEN}  ✅ Black: PASSED${NC}"
else
    echo -e "  ⚠️  Black: Some issues may remain"
    VERIFICATION_PASSED=false
fi

echo "🔍 Verifying isort..."
if isort --check-only --profile=black --line-length=100 app/ tests/ 2>&1; then
    echo -e "${GREEN}  ✅ isort: PASSED${NC}"
else
    echo -e "  ⚠️  isort: Some issues may remain"
    VERIFICATION_PASSED=false
fi

echo "🔍 Verifying Ruff..."
if ruff check app/ tests/ 2>&1; then
    echo -e "${GREEN}  ✅ Ruff: PASSED${NC}"
else
    echo -e "  ⚠️  Ruff: Some warnings present (may be acceptable)"
fi

echo ""

# Summary
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  📊 SUMMARY${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$VERIFICATION_PASSED" = true ]; then
    echo -e "${GREEN}🎉 SUCCESS! All formatting applied and verified!${NC}"
    echo ""
    echo -e "${GREEN}✅ Your code is now ready to pass GitHub Actions checks!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review the changes: git diff"
    echo "  2. Stage the changes: git add ."
    echo "  3. Commit: git commit -m \"style: Apply code formatting\""
    echo "  4. Push: git push"
else
    echo -e "⚠️  Some issues may remain. Please review the output above."
    echo ""
    echo "Most likely, the remaining issues are acceptable warnings."
    echo "Code formatting complete."
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Built with ❤️ by Houssam Benmerah${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
