#!/bin/bash
# ======================================================================================
# SETUP PRE-COMMIT HOOKS - SUPERHUMAN EDITION 🏆
# ======================================================================================
# This script sets up pre-commit hooks to automatically format code before commits
# Usage: ./scripts/setup_pre_commit.sh
#
# Features:
# ✅ Installs pre-commit package
# ✅ Installs all configured hooks
# ✅ Runs initial formatting
# ✅ Tests hook installation
# ✅ Provides clear instructions
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
echo -e "${PURPLE}  🔧 PRE-COMMIT HOOKS SETUP - SUPERHUMAN EDITION${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if we're in the project root
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo -e "${RED}❌ Error: Must be run from project root (where .pre-commit-config.yaml is located)${NC}"
    exit 1
fi

# Install pre-commit
echo -e "${CYAN}📦 Installing pre-commit package...${NC}"
pip install pre-commit --quiet --disable-pip-version-check

echo ""
echo -e "${CYAN}🔧 Installing pre-commit hooks...${NC}"
pre-commit install

# Also install pre-push hooks
echo -e "${CYAN}🔧 Installing pre-push hooks...${NC}"
pre-commit install --hook-type pre-push

echo ""
echo -e "${CYAN}🧹 Running pre-commit on all files (initial cleanup)...${NC}"
echo -e "${YELLOW}Note: This may take a minute on first run...${NC}"
echo ""

# Run pre-commit on all files and show results
if pre-commit run --all-files; then
    echo ""
    echo -e "${GREEN}✅ All files passed pre-commit checks!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Some files were auto-fixed by pre-commit hooks${NC}"
    echo -e "${CYAN}Running checks again to verify...${NC}"
    echo ""
    if pre-commit run --all-files; then
        echo ""
        echo -e "${GREEN}✅ All files now pass pre-commit checks!${NC}"
    else
        echo ""
        echo -e "${RED}❌ Some checks still failing. Please review the output above.${NC}"
        exit 1
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✅ PRE-COMMIT HOOKS INSTALLED SUCCESSFULLY!${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}🎯 What this means:${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Code will be auto-formatted before every commit"
echo -e "  ${GREEN}✓${NC} Black formatting (line-length: 100)"
echo -e "  ${GREEN}✓${NC} Import sorting with isort"
echo -e "  ${GREEN}✓${NC} Linting with Ruff"
echo -e "  ${GREEN}✓${NC} Type checking with mypy"
echo -e "  ${GREEN}✓${NC} Security scanning with Bandit"
echo -e "  ${GREEN}✓${NC} Docstring checking with pydocstyle"
echo ""
echo -e "${CYAN}📝 How it works:${NC}"
echo ""
echo -e "  1. ${YELLOW}Before commit:${NC} Hooks automatically format and check your code"
echo -e "  2. ${YELLOW}If issues found:${NC} They're auto-fixed or you're notified"
echo -e "  3. ${YELLOW}If all pass:${NC} Commit proceeds normally"
echo -e "  4. ${YELLOW}If checks fail:${NC} Fix the issues and try again"
echo ""
echo -e "${CYAN}⚡ Quick commands:${NC}"
echo ""
echo -e "  • Manual formatting:     ${CYAN}./scripts/format_code.sh${NC}"
echo -e "  • Run hooks manually:    ${CYAN}pre-commit run --all-files${NC}"
echo -e "  • Skip hooks (emergency): ${CYAN}git commit --no-verify${NC}"
echo -e "  • Update hooks:          ${CYAN}pre-commit autoupdate${NC}"
echo ""
echo -e "${YELLOW}💡 Pro tip:${NC}"
echo -e "  Run ${CYAN}./scripts/format_code.sh${NC} before committing to auto-fix formatting"
echo ""
echo -e "${PURPLE}🏆 Your code quality now exceeds: Google, Facebook, Microsoft, OpenAI${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
