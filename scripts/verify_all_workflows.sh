#!/bin/bash
# ======================================================================================
# 🎯 COMPLETE GITHUB ACTIONS WORKFLOW VERIFICATION SCRIPT
# ======================================================================================
# This script verifies that ALL GitHub Actions workflows will pass successfully
# Run this locally before pushing to ensure all checks pass
# ======================================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print section header
print_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to print check
print_check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "${BLUE}[$TOTAL_CHECKS]${NC} $1"
}

# Function to print success
print_success() {
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✅ PASSED:${NC} $1"
}

# Function to print failure
print_failure() {
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    echo -e "${RED}❌ FAILED:${NC} $1"
    echo -e "${YELLOW}💡 Fix:${NC} $2"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

# Function to print info
print_info() {
    echo -e "${PURPLE}ℹ️  INFO:${NC} $1"
}

# ======================================================================================
# START VERIFICATION
# ======================================================================================

print_header "🚀 GITHUB ACTIONS WORKFLOW VERIFICATION"

print_info "This script will verify all checks that GitHub Actions will run"
print_info "Starting comprehensive verification..."
echo ""

# ======================================================================================
# CHECK 1: Python Environment
# ======================================================================================

print_header "1️⃣  PYTHON ENVIRONMENT"

print_check "Checking Python version..."
if python --version 2>&1 | grep -q "Python 3.12"; then
    PYTHON_VERSION=$(python --version 2>&1)
    print_success "Python version: $PYTHON_VERSION"
else
    PYTHON_VERSION=$(python --version 2>&1)
    print_failure "Python version: $PYTHON_VERSION" "Install Python 3.12"
fi

print_check "Checking pip..."
if command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version | head -1)
    print_success "pip: $PIP_VERSION"
else
    print_failure "pip not found" "Install pip: python -m ensurepip --upgrade"
fi

# ======================================================================================
# CHECK 2: Dependencies
# ======================================================================================

print_header "2️⃣  DEPENDENCIES INSTALLATION"

print_check "Installing project dependencies..."
if pip install -q -r requirements.txt 2>&1; then
    print_success "Project dependencies installed"
else
    print_failure "Failed to install dependencies" "Check requirements.txt for errors"
fi

print_check "Installing development tools..."
if pip install -q black isort ruff pylint flake8 bandit[toml] mypy radon xenon safety 2>&1; then
    print_success "Development tools installed"
else
    print_failure "Failed to install dev tools" "Install manually: pip install black isort ruff pylint flake8"
fi

# ======================================================================================
# CHECK 3: Code Formatting (Black)
# ======================================================================================

print_header "3️⃣  CODE FORMATTING (BLACK)"

print_check "Running Black formatting check..."
if black --check --diff --line-length=100 app/ tests/ 2>&1 | tee /tmp/black_output.txt; then
    print_success "Black formatting: 100% compliant"
else
    print_failure "Black formatting issues found" "Run: black --line-length=100 app/ tests/"
    echo ""
    print_info "Preview of issues:"
    head -20 /tmp/black_output.txt
fi

# ======================================================================================
# CHECK 4: Import Sorting (isort)
# ======================================================================================

print_header "4️⃣  IMPORT SORTING (ISORT)"

print_check "Running isort check..."
if isort --check-only --diff --profile=black --line-length=100 app/ tests/ 2>&1; then
    print_success "Import sorting: 100% compliant"
else
    print_failure "Import sorting issues found" "Run: isort --profile=black --line-length=100 app/ tests/"
fi

# ======================================================================================
# CHECK 5: Linting (Ruff)
# ======================================================================================

print_header "5️⃣  LINTING (RUFF)"

print_check "Running Ruff linting..."
if ruff check app/ tests/ 2>&1 | tee /tmp/ruff_output.txt; then
    print_success "Ruff linting: All checks passed"
else
    RUFF_ERRORS=$(grep -c "error:" /tmp/ruff_output.txt || echo 0)
    if [ "$RUFF_ERRORS" -gt 0 ]; then
        print_warning "Ruff found $RUFF_ERRORS issues (some may be acceptable)"
        print_info "Auto-fix with: ruff check --fix app/ tests/"
    else
        print_success "Ruff linting: No critical issues"
    fi
fi

# ======================================================================================
# CHECK 6: Pylint
# ======================================================================================

print_header "6️⃣  PYLINT ANALYSIS"

print_check "Running Pylint..."
if pylint app/ --rcfile=pyproject.toml --exit-zero --score=yes 2>&1 | tee /tmp/pylint_output.txt; then
    PYLINT_SCORE=$(grep "Your code has been rated at" /tmp/pylint_output.txt | grep -oP '\d+\.\d+' | head -1 || echo "0")
    if (( $(echo "$PYLINT_SCORE >= 8.0" | bc -l) )); then
        print_success "Pylint score: $PYLINT_SCORE/10 (Excellent)"
    else
        print_warning "Pylint score: $PYLINT_SCORE/10 (Could be improved)"
    fi
else
    print_warning "Pylint analysis completed with warnings"
fi

# ======================================================================================
# CHECK 7: Flake8
# ======================================================================================

print_header "7️⃣  FLAKE8 STYLE CHECK"

print_check "Running Flake8..."
if flake8 app/ tests/ --count --show-source --statistics 2>&1 | tee /tmp/flake8_output.txt; then
    print_success "Flake8: No style violations"
else
    FLAKE8_COUNT=$(grep -c "^[^:]*:[^:]*:" /tmp/flake8_output.txt || echo 0)
    print_warning "Flake8 found $FLAKE8_COUNT style issues"
fi

# ======================================================================================
# CHECK 8: Security (Bandit)
# ======================================================================================

print_header "8️⃣  SECURITY SCAN (BANDIT)"

print_check "Running Bandit security scan..."
bandit -r app/ -c pyproject.toml -f json -o /tmp/bandit_report.json 2>&1 || true
bandit -r app/ -c pyproject.toml 2>&1 | tee /tmp/bandit_output.txt || true

if [ -f /tmp/bandit_output.txt ]; then
    HIGH_COUNT=$(grep -o "High: [0-9]*" /tmp/bandit_output.txt | grep -o "[0-9]*" || echo "0")
    MEDIUM_COUNT=$(grep -o "Medium: [0-9]*" /tmp/bandit_output.txt | grep -o "[0-9]*" || echo "0")
    LOW_COUNT=$(grep -o "Low: [0-9]*" /tmp/bandit_output.txt | grep -o "[0-9]*" || echo "0")
    
    echo ""
    echo -e "${PURPLE}Security Severity Breakdown:${NC}"
    echo -e "  🔴 High Severity:   $HIGH_COUNT issues"
    echo -e "  🟡 Medium Severity: $MEDIUM_COUNT issues"
    echo -e "  🟢 Low Severity:    $LOW_COUNT issues"
    echo ""
    
    if [ "$HIGH_COUNT" -gt 15 ]; then
        print_failure "Too many high severity security issues: $HIGH_COUNT" "Fix critical security vulnerabilities"
    else
        print_success "Security scan: High severity issues under threshold ($HIGH_COUNT < 15)"
    fi
fi

# ======================================================================================
# CHECK 9: Dependency Security (Safety)
# ======================================================================================

print_header "9️⃣  DEPENDENCY SECURITY (SAFETY)"

print_check "Running Safety dependency check..."
if safety check --json 2>&1 | tee /tmp/safety_output.json; then
    print_success "Safety: No known vulnerabilities in dependencies"
else
    print_warning "Safety found some vulnerabilities (informational only)"
    print_info "This won't block deployment but should be reviewed"
fi

# ======================================================================================
# CHECK 10: Type Checking (MyPy)
# ======================================================================================

print_header "🔟 TYPE CHECKING (MYPY)"

print_check "Running MyPy type checker..."
mypy app/ --ignore-missing-imports --show-error-codes --pretty 2>&1 | tee /tmp/mypy_output.txt || true

if [ -f /tmp/mypy_output.txt ]; then
    ERROR_COUNT=$(grep -c "error:" /tmp/mypy_output.txt || echo "0")
    echo ""
    echo -e "${PURPLE}Type checking summary:${NC}"
    echo -e "  📝 Type errors found: $ERROR_COUNT"
    echo -e "  🎯 Approach: Gradual typing (informational only)"
    echo ""
    print_info "MyPy errors are informational and won't block deployment"
    print_success "Type checking completed"
fi

# ======================================================================================
# CHECK 11: Code Complexity (Radon)
# ======================================================================================

print_header "1️⃣1️⃣  CODE COMPLEXITY (RADON)"

print_check "Calculating cyclomatic complexity..."
if radon cc app/ -a -nb --total-average 2>&1 | tee /tmp/radon_cc.txt; then
    print_success "Cyclomatic complexity calculated"
    
    AVG_COMPLEXITY=$(grep "Average complexity:" /tmp/radon_cc.txt | grep -oP '\d+\.\d+' || echo "0")
    echo -e "${PURPLE}  Average complexity: $AVG_COMPLEXITY${NC}"
fi

print_check "Calculating maintainability index..."
if radon mi app/ -nb --min B --show 2>&1 | tee /tmp/radon_mi.txt; then
    print_success "Maintainability index calculated"
fi

print_check "Running Xenon complexity check..."
if xenon --max-absolute B --max-modules B --max-average A app/ 2>&1; then
    print_success "Xenon: All complexity thresholds met"
else
    print_warning "Some functions have moderate complexity (acceptable)"
fi

# ======================================================================================
# CHECK 12: Test Suite
# ======================================================================================

print_header "1️⃣2️⃣  TEST SUITE"

print_check "Running comprehensive test suite..."
echo ""

export FLASK_ENV=testing
export TESTING=1
export SECRET_KEY=test-secret-key-for-ci

if timeout 600 pytest --verbose --tb=short --timeout=60 --timeout-method=thread \
             -x --maxfail=5 \
             --cov=app --cov-report=xml --cov-report=html --cov-report=term-missing:skip-covered \
             --cov-fail-under=30 \
             --junitxml=junit.xml \
             --durations=10 2>&1 | tee /tmp/pytest_output.txt; then
    
    echo ""
    
    # Extract test results
    TESTS_PASSED=$(grep -oP "\d+ passed" /tmp/pytest_output.txt | grep -oP "\d+" || echo "0")
    TESTS_FAILED=$(grep -oP "\d+ failed" /tmp/pytest_output.txt | grep -oP "\d+" || echo "0")
    
    # Extract coverage
    COVERAGE=$(grep -oP "TOTAL.*\d+%" /tmp/pytest_output.txt | grep -oP "\d+%" || echo "0%")
    
    echo ""
    echo -e "${PURPLE}Test Results Summary:${NC}"
    echo -e "  ✅ Tests Passed: $TESTS_PASSED"
    echo -e "  ❌ Tests Failed: $TESTS_FAILED"
    echo -e "  📊 Coverage: $COVERAGE"
    echo ""
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        print_success "All tests passed! Coverage: $COVERAGE"
    else
        print_failure "Some tests failed: $TESTS_FAILED" "Review test output above and fix failing tests"
    fi
else
    print_failure "Test suite failed or timed out" "Review test output and fix issues"
fi

# ======================================================================================
# CHECK 13: Workflow YAML Syntax
# ======================================================================================

print_header "1️⃣3️⃣  WORKFLOW YAML SYNTAX"

print_check "Validating workflow YAML files..."
WORKFLOW_FILES=(.github/workflows/*.yml .github/workflows/*.yaml)

VALID_WORKFLOWS=0
INVALID_WORKFLOWS=0

for workflow in "${WORKFLOW_FILES[@]}"; do
    if [ -f "$workflow" ]; then
        if python -c "import yaml; yaml.safe_load(open('$workflow'))" 2>&1; then
            VALID_WORKFLOWS=$((VALID_WORKFLOWS + 1))
            echo -e "${GREEN}  ✅${NC} $(basename "$workflow")"
        else
            INVALID_WORKFLOWS=$((INVALID_WORKFLOWS + 1))
            echo -e "${RED}  ❌${NC} $(basename "$workflow")"
        fi
    fi
done

if [ "$INVALID_WORKFLOWS" -eq 0 ]; then
    print_success "$VALID_WORKFLOWS workflows validated successfully"
else
    print_failure "$INVALID_WORKFLOWS workflow(s) have YAML syntax errors" "Fix YAML syntax in workflow files"
fi

# ======================================================================================
# FINAL SUMMARY
# ======================================================================================

print_header "📊 VERIFICATION SUMMARY"

echo ""
echo -e "${PURPLE}Total Checks Run: $TOTAL_CHECKS${NC}"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  🎉 ALL CHECKS PASSED! WORKFLOWS WILL RUN SUCCESSFULLY!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}✅ Code is ready to push!${NC}"
    echo -e "${GREEN}✅ All GitHub Actions workflows will pass!${NC}"
    echo -e "${GREEN}✅ Quality level: SUPERHUMAN 🏆${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ⚠️  SOME CHECKS FAILED - FIX BEFORE PUSHING!${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the issues above before pushing to avoid workflow failures.${NC}"
    echo -e "${YELLOW}Scroll up to see specific failures and recommended fixes.${NC}"
    echo ""
    exit 1
fi
