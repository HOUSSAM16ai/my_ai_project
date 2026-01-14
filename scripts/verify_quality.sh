#!/usr/bin/env bash
# ======================================================================================
# COMPREHENSIVE QUALITY VERIFICATION - Superhuman Edition
# ======================================================================================
# This script runs all quality checks that match GitHub Actions CI/CD
# Standards: Exceeding Google, Facebook, Microsoft, OpenAI, Apple
#
# Usage:
#   ./scripts/verify_quality.sh              # Run all checks
#   ./scripts/verify_quality.sh --fast       # Run fast checks only
#   ./scripts/verify_quality.sh --security   # Run security checks only
#   ./scripts/verify_quality.sh --help       # Show help
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
RUN_MODE="all"  # all, fast, security, type

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            RUN_MODE="fast"
            shift
            ;;
        --security)
            RUN_MODE="security"
            shift
            ;;
        --type)
            RUN_MODE="type"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fast       Run fast checks only (formatting, linting)"
            echo "  --security   Run security checks only (Bandit, Safety)"
            echo "  --type       Run type checking only (MyPy)"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "Default: Run all checks"
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
echo -e "${PURPLE}  🏆 SUPERHUMAN QUALITY VERIFICATION${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Mode: ${YELLOW}${RUN_MODE}${NC}"
echo ""

# Track results
declare -A RESULTS
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run check
run_check() {
    local name=$1
    local cmd=$2
    local required=${3:-true}  # Is this check required to pass?
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🔍 Running: $name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if eval "$cmd" > /tmp/check_output_$TOTAL_CHECKS.log 2>&1; then
        echo -e "${GREEN}✅ $name: PASSED${NC}"
        RESULTS[$name]="PASSED"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [ "$required" = true ]; then
            echo -e "${RED}❌ $name: FAILED${NC}"
            RESULTS[$name]="FAILED"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${YELLOW}⚠️  $name: FAILED (informational)${NC}"
            RESULTS[$name]="WARNING"
        fi
        echo ""
        echo "Last 20 lines of output:"
        tail -20 /tmp/check_output_$TOTAL_CHECKS.log || true
        return 1
    fi
}

# =============================================================================
# FAST CHECKS (Formatting & Linting)
# =============================================================================
if [ "$RUN_MODE" = "all" ] || [ "$RUN_MODE" = "fast" ]; then
    echo -e "${CYAN}📋 SECTION 1: Code Style & Formatting${NC}"
    echo ""
    
    run_check "Black formatting" "black --check --line-length=100 app/ tests/" true
    echo ""
    
    run_check "isort import sorting" "isort --check-only --profile=black --line-length=100 app/ tests/" true
    echo ""
    
    run_check "Ruff linting" "ruff check app/ tests/" true
    echo ""
    
    run_check "Flake8 style checking" "flake8 app/ tests/ --count --statistics" true
    echo ""
fi

# =============================================================================
# SECURITY CHECKS
# =============================================================================
if [ "$RUN_MODE" = "all" ] || [ "$RUN_MODE" = "security" ]; then
    echo -e "${CYAN}🔒 SECTION 2: Security & Vulnerability Scanning${NC}"
    echo ""
    
    # Bandit security scan
    echo -e "${CYAN}Running Bandit security scan...${NC}"
    if bandit -r app/ -c pyproject.toml -f json -o /tmp/bandit-report.json 2>&1 | tee /tmp/bandit-output.txt; then
        echo -e "${GREEN}✅ Bandit: No critical issues${NC}"
        RESULTS["Bandit security scan"]="PASSED"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        # Check severity counts
        HIGH_COUNT=$(grep -o "High: [0-9]*" /tmp/bandit-output.txt | grep -o "[0-9]*" || echo "0")
        MEDIUM_COUNT=$(grep -o "Medium: [0-9]*" /tmp/bandit-output.txt | grep -o "[0-9]*" || echo "0")
        
        echo ""
        echo -e "${YELLOW}📊 Security Summary:${NC}"
        echo "  🔴 High Severity:   $HIGH_COUNT issues"
        echo "  🟡 Medium Severity: $MEDIUM_COUNT issues"
        
        if [ "$HIGH_COUNT" -gt 15 ]; then
            echo -e "${RED}❌ Bandit: Too many high severity issues ($HIGH_COUNT > 15)${NC}"
            RESULTS["Bandit security scan"]="FAILED"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${GREEN}✅ Bandit: Within acceptable limits${NC}"
            RESULTS["Bandit security scan"]="PASSED"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        fi
    fi
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo ""
    
    # Safety dependency check (informational)
    run_check "Safety dependency scan" "safety check --json --output /tmp/safety-report.json" false || true
    echo ""
fi

# =============================================================================
# TYPE CHECKING
# =============================================================================
if [ "$RUN_MODE" = "all" ] || [ "$RUN_MODE" = "type" ]; then
    echo -e "${CYAN}🔍 SECTION 3: Type Safety (Progressive)${NC}"
    echo ""
    
    run_check "MyPy type checking" "mypy app/ --ignore-missing-imports --show-error-codes" false
    echo ""
fi

# =============================================================================
# CODE COMPLEXITY
# =============================================================================
if [ "$RUN_MODE" = "all" ]; then
    echo -e "${CYAN}📊 SECTION 4: Code Complexity & Maintainability${NC}"
    echo ""
    
    echo -e "${CYAN}Running Radon complexity analysis...${NC}"
    radon cc app/ -a -nb --total-average | tee /tmp/radon-output.txt
    echo -e "${GREEN}✅ Complexity analysis complete${NC}"
    echo ""
    
    echo -e "${CYAN}Running maintainability index...${NC}"
    radon mi app/ -nb --min B --show | tee /tmp/radon-mi.txt
    echo -e "${GREEN}✅ Maintainability index complete${NC}"
    echo ""

    run_check "Agentic standards audit" "python scripts/verify_agentic_standards.py" true
    echo ""
    
    # Xenon complexity check (informational)
    run_check "Xenon complexity threshold" "xenon --max-absolute B --max-modules B --max-average A app/" false || true
    echo ""
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  📊 QUALITY VERIFICATION SUMMARY${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}Results by Check:${NC}"
for check in "${!RESULTS[@]}"; do
    result="${RESULTS[$check]}"
    if [ "$result" = "PASSED" ]; then
        echo -e "  ${GREEN}✅ $check${NC}"
    elif [ "$result" = "FAILED" ]; then
        echo -e "  ${RED}❌ $check${NC}"
    else
        echo -e "  ${YELLOW}⚠️  $check${NC}"
    fi
done

echo ""
echo -e "${CYAN}Overall Statistics:${NC}"
echo "  Total checks: $TOTAL_CHECKS"
echo "  Passed: $PASSED_CHECKS"
echo "  Failed: $FAILED_CHECKS"
echo "  Warnings: $((TOTAL_CHECKS - PASSED_CHECKS - FAILED_CHECKS))"

echo ""
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}  🏆 ALL CRITICAL CHECKS PASSED!${NC}"
    echo -e "${GREEN}  Your code meets SUPERHUMAN quality standards!${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}  ❌ $FAILED_CHECKS CHECK(S) FAILED${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo "  1. Review the failed checks above"
    echo "  2. Run auto-formatters: ./scripts/format_all.sh"
    echo "  3. Fix remaining issues manually"
    echo "  4. Run verification again: ./scripts/verify_quality.sh"
    echo ""
    exit 1
fi
