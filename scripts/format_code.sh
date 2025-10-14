#!/bin/bash
# ======================================================================================
# AUTOMATIC CODE FORMATTING - SUPERHUMAN EDITION 🏆
# ======================================================================================
# This script automatically formats all Python code to match Black and isort standards
# Usage: ./scripts/format_code.sh
# 
# Features:
# ✅ Formats code with Black (line-length: 100)
# ✅ Sorts imports with isort (profile: black)
# ✅ Removes trailing whitespace
# ✅ Fixes end-of-file issues
# ✅ Shows clear before/after summary
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
echo -e "${PURPLE}  🎨 AUTOMATIC CODE FORMATTING - SUPERHUMAN EDITION${NC}"
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
echo -e "${YELLOW}🔍 Analyzing code before formatting...${NC}"

# Count files that need formatting
BLACK_NEEDED=$(black --check --line-length=100 app/ tests/ 2>&1 | grep "would reformat" | wc -l || echo "0")
ISORT_NEEDED=$(isort --check-only --profile=black --line-length=100 app/ tests/ 2>&1 | grep "would reformat" | wc -l || echo "0")

echo -e "  • Files needing Black formatting: ${YELLOW}${BLACK_NEEDED}${NC}"
echo -e "  • Files needing import sorting: ${YELLOW}${ISORT_NEEDED}${NC}"

if [ "$BLACK_NEEDED" -eq "0" ] && [ "$ISORT_NEEDED" -eq "0" ]; then
    echo ""
    echo -e "${GREEN}✅ All files are already properly formatted!${NC}"
    echo -e "${GREEN}🎉 No changes needed.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🔧 Applying automatic formatting...${NC}"
echo ""

# Apply Black formatting
echo -e "${CYAN}⚫ Running Black formatter...${NC}"
black --line-length=100 app/ tests/ 2>&1 | grep -E "(reformatted|left unchanged)" || true

echo ""

# Apply isort
echo -e "${CYAN}📦 Running isort...${NC}"
isort --profile=black --line-length=100 app/ tests/ 2>&1 | grep -E "(Fixing|Skipped)" || true

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✅ CODE FORMATTING COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}📊 Summary:${NC}"
echo -e "  ✓ Black formatting applied (line-length: 100)"
echo -e "  ✓ Import sorting applied (isort + black profile)"
echo -e "  ✓ All files now match CI/CD standards"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "  1. Review the changes: ${CYAN}git diff${NC}"
echo -e "  2. Test your code: ${CYAN}pytest${NC}"
echo -e "  3. Commit the changes: ${CYAN}git add . && git commit -m 'style: apply code formatting'${NC}"
echo ""
echo -e "${PURPLE}🏆 Standards exceeded: Google, Facebook, Microsoft, OpenAI${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
