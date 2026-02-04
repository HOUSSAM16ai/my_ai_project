#!/bin/bash
# =============================================================================
# Comprehensive Test Execution Script
# =============================================================================
# Runs all test types: unit, property-based, fuzzing, integration, security
# Generates coverage reports and mutation testing results
# Target: 100% coverage + 100% mutation score

set -e  # Exit on error

echo "🚀 Starting Comprehensive Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create reports directory
mkdir -p reports/comprehensive

echo ""
echo "📋 Step 1: Running Unit Tests"
echo "------------------------------"
python -m pytest tests/ \
    -v \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:reports/comprehensive/coverage_html \
    --cov-report=xml:reports/comprehensive/coverage.xml \
    --cov-report=json:reports/comprehensive/coverage.json \
    --junit-xml=reports/comprehensive/junit.xml \
    --durations=20 \
    -m "not fuzz" \
    || { echo -e "${RED}❌ Unit tests failed${NC}"; exit 1; }

echo ""
echo "📊 Step 2: Coverage Analysis"
echo "----------------------------"
python -c "
import json
with open('reports/comprehensive/coverage.json') as f:
    data = json.load(f)
    coverage = data['totals']['percent_covered']
    print(f'Current Coverage: {coverage:.2f}%')
    if coverage < 100:
        print(f'⚠️  Coverage is below 100% (current: {coverage:.2f}%)')
    else:
        print('✅ 100% coverage achieved!')
"

echo ""
echo "🔬 Step 3: Property-Based Tests"
echo "--------------------------------"
python -m pytest tests/property_based/ \
    -v \
    --hypothesis-show-statistics \
    || { echo -e "${YELLOW}⚠️  Property-based tests had issues${NC}"; }

echo ""
echo "💥 Step 4: Fuzzing Tests"
echo "------------------------"
python -m pytest tests/fuzzing/ \
    -v \
    -m fuzz \
    --timeout=300 \
    || { echo -e "${YELLOW}⚠️  Fuzzing tests had issues${NC}"; }

echo ""
echo "🔗 Step 5: Integration Tests"
echo "-----------------------------"
python -m pytest tests/integration/ \
    -v \
    || { echo -e "${RED}❌ Integration tests failed${NC}"; exit 1; }

echo ""
echo "🔒 Step 6: Security Tests"
echo "-------------------------"
python -m pytest tests/security/ \
    -v \
    -m security \
    || { echo -e "${RED}❌ Security tests failed${NC}"; exit 1; }

echo ""
echo "🧬 Step 7: Mutation Testing"
echo "---------------------------"
echo "Running mutation tests on critical modules..."

# Run mutation testing on validators
mutmut run \
    --paths-to-mutate=app/validators/ \
    --tests-dir=tests/validators/ \
    --runner="python -m pytest -x" \
    || { echo -e "${YELLOW}⚠️  Some mutations survived${NC}"; }

# Generate mutation report
mutmut results > reports/comprehensive/mutation_results.txt || true
mutmut html --directory reports/comprehensive/mutation_html || true

echo ""
echo "📈 Step 8: Generating Final Report"
echo "-----------------------------------"

python -c "
import json
import os
from pathlib import Path

print('\\n' + '='*60)
print('COMPREHENSIVE TEST REPORT')
print('='*60)

# Coverage
if Path('reports/comprehensive/coverage.json').exists():
    with open('reports/comprehensive/coverage.json') as f:
        data = json.load(f)
        coverage = data['totals']['percent_covered']
        lines_covered = data['totals']['covered_lines']
        lines_total = data['totals']['num_statements']

        print(f'\\n📊 Coverage:')
        print(f'  Total Lines: {lines_total}')
        print(f'  Covered Lines: {lines_covered}')
        print(f'  Coverage: {coverage:.2f}%')

        if coverage >= 100:
            print('  ✅ 100% coverage achieved!')
        elif coverage >= 90:
            print(f'  ⚠️  Coverage: {coverage:.2f}% (target: 100%)')
        else:
            print(f'  ❌ Coverage: {coverage:.2f}% (target: 100%)')

# Test results
if Path('reports/comprehensive/junit.xml').exists():
    import xml.etree.ElementTree as ET
    tree = ET.parse('reports/comprehensive/junit.xml')
    root = tree.getroot()

    tests = int(root.attrib.get('tests', 0))
    failures = int(root.attrib.get('failures', 0))
    errors = int(root.attrib.get('errors', 0))
    skipped = int(root.attrib.get('skipped', 0))

    print(f'\\n🧪 Test Results:')
    print(f'  Total Tests: {tests}')
    print(f'  Passed: {tests - failures - errors - skipped}')
    print(f'  Failed: {failures}')
    print(f'  Errors: {errors}')
    print(f'  Skipped: {skipped}')

    if failures == 0 and errors == 0:
        print('  ✅ All tests passed!')
    else:
        print(f'  ❌ {failures + errors} tests failed')

# Mutation testing
if Path('reports/comprehensive/mutation_results.txt').exists():
    with open('reports/comprehensive/mutation_results.txt') as f:
        content = f.read()
        print(f'\\n🧬 Mutation Testing:')
        print(f'  See reports/comprehensive/mutation_results.txt for details')

print('\\n' + '='*60)
print('Reports generated in: reports/comprehensive/')
print('  - coverage_html/index.html')
print('  - coverage.xml')
print('  - junit.xml')
print('  - mutation_html/index.html')
print('='*60)
"

echo ""
echo -e "${GREEN}✅ Comprehensive test suite completed!${NC}"
echo "📁 Reports available in: reports/comprehensive/"
