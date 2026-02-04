#!/bin/bash
# ======================================================================================
# Auto-Fix Script - Automatically fix code quality issues
# ======================================================================================
# Usage: ./scripts/ci/auto-fix.sh
# ======================================================================================

set -e

echo "🔧 Auto-fixing code quality issues..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Black formatting
echo ""
echo "⚫ Applying Black formatting..."
black --line-length=100 app/ tests/
echo -e "${GREEN}✅ Black formatting applied${NC}"

# 2. Import sorting
echo ""
echo "📦 Sorting imports with isort..."
isort --profile=black --line-length=100 app/ tests/
echo -e "${GREEN}✅ Import sorting applied${NC}"

# 3. Ruff auto-fix
echo ""
echo "⚡ Auto-fixing Ruff issues..."
ruff check --fix app/ tests/ || true
echo -e "${GREEN}✅ Ruff auto-fixes applied${NC}"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Auto-fix complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}💡 Tip: Review the changes with 'git diff' before committing${NC}"
echo ""
