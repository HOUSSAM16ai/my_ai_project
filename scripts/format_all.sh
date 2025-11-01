#!/usr/bin/env bash
# ======================================================================================
# COMPREHENSIVE CODE FORMATTER - Superhuman Edition
# ======================================================================================
# This script applies all code formatters in the correct order
# Standards: Google, Facebook, Microsoft, OpenAI, Apple
#
# Usage:
#   ./scripts/format_all.sh              # Format all code
#   ./scripts/format_all.sh --check      # Check only (no changes)
#   ./scripts/format_all.sh --help       # Show help
# ======================================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Change to project root
cd "${PROJECT_ROOT}"

# Configuration
CHECK_ONLY=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --check       Check formatting without making changes"
            echo "  -v, --verbose Show detailed output"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  🎨 SUPERHUMAN CODE FORMATTER${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if tools are installed
echo -e "${CYAN}🔍 Checking required tools...${NC}"
TOOLS_MISSING=false

for tool in black isort ruff; do
    if ! command -v $tool &> /dev/null; then
        echo -e "${RED}❌ $tool is not installed${NC}"
        TOOLS_MISSING=true
    else
        echo -e "${GREEN}✅ $tool is installed${NC}"
    fi
done

if [ "$TOOLS_MISSING" = true ]; then
    echo ""
    echo -e "${YELLOW}📦 Install missing tools with:${NC}"
    echo "    pip install black isort ruff"
    exit 1
fi

echo ""

# Function to run formatter
run_formatter() {
    local name=$1
    local cmd=$2
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🔧 Running $name...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ "$VERBOSE" = true ]; then
        echo "Command: $cmd"
    fi
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ $name: PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: FAILED${NC}"
        return 1
    fi
}

# Track overall status
OVERALL_STATUS=0

# Step 1: Black (code formatting)
if [ "$CHECK_ONLY" = true ]; then
    run_formatter "Black (check)" "black --check --diff --color --line-length=100 app/ tests/" || OVERALL_STATUS=1
else
    run_formatter "Black (format)" "black --line-length=100 app/ tests/" || OVERALL_STATUS=1
fi

echo ""

# Step 2: isort (import sorting)
if [ "$CHECK_ONLY" = true ]; then
    run_formatter "isort (check)" "isort --check-only --diff --profile=black --line-length=100 app/ tests/" || OVERALL_STATUS=1
else
    run_formatter "isort (sort)" "isort --profile=black --line-length=100 app/ tests/" || OVERALL_STATUS=1
fi

echo ""

# Step 3: Ruff (linting with auto-fix)
if [ "$CHECK_ONLY" = true ]; then
    run_formatter "Ruff (check)" "ruff check app/ tests/" || OVERALL_STATUS=1
else
    run_formatter "Ruff (fix)" "ruff check app/ tests/ --fix" || OVERALL_STATUS=1
fi

echo ""

# Print summary
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}  ✅ ALL FORMATTERS PASSED!${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    if [ "$CHECK_ONLY" = false ]; then
        echo -e "${CYAN}📊 Summary:${NC}"
        echo "  • Code formatted with Black (line-length: 100)"
        echo "  • Imports sorted with isort (profile: black)"
        echo "  • Linting issues fixed with Ruff"
        echo ""
        echo -e "${GREEN}🎉 Your code is now formatted to superhuman standards!${NC}"
    else
        echo -e "${GREEN}✅ All formatting checks passed!${NC}"
        echo "   Your code already meets superhuman standards."
    fi
else
    echo -e "${RED}  ❌ SOME FORMATTERS FAILED${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    if [ "$CHECK_ONLY" = true ]; then
        echo "  1. Run without --check to auto-fix issues:"
        echo "     ./scripts/format_all.sh"
        echo ""
        echo "  2. Or run formatters individually:"
        echo "     black --line-length=100 app/ tests/"
        echo "     isort --profile=black --line-length=100 app/ tests/"
        echo "     ruff check app/ tests/ --fix"
    else
        echo "  1. Review the errors above"
        echo "  2. Fix any remaining issues manually"
        echo "  3. Run again to verify:"
        echo "     ./scripts/format_all.sh --check"
    fi
fi

echo ""
exit $OVERALL_STATUS
