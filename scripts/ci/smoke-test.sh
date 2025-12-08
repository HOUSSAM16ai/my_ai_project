#!/bin/bash
# ======================================================================================
# GitLab CI/CD Smoke Test Script
# ======================================================================================
# Quick smoke tests after deployment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-development}"
URL="${2:-}"

if [[ -z "${URL}" ]]; then
    case "${ENVIRONMENT}" in
        development)
            URL="https://dev.cogniforge.com"
            ;;
        staging)
            URL="https://staging.cogniforge.com"
            ;;
        production)
            URL="https://cogniforge.com"
            ;;
    esac
fi

echo -e "${GREEN}💨 Running smoke tests for ${ENVIRONMENT}${NC}"
echo "   URL: ${URL}"
echo ""

FAILED_TESTS=0
PASSED_TESTS=0

# Test function
run_test() {
    local test_name=$1
    local endpoint=$2
    local expected_status=$3
    
    echo -e "${YELLOW}🧪 ${test_name}${NC}"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}${endpoint}")
    
    if [[ "${HTTP_CODE}" == "${expected_status}" ]]; then
        echo -e "${GREEN}   ✅ PASS (${HTTP_CODE})${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}   ❌ FAIL (expected ${expected_status}, got ${HTTP_CODE})${NC}"
        ((FAILED_TESTS++))
    fi
}

# Run tests
run_test "Health Check" "/health" "200"
run_test "API Root" "/api" "200"
run_test "API Docs" "/docs" "200"
run_test "OpenAPI Schema" "/openapi.json" "200"
run_test "404 Handling" "/nonexistent" "404"

# Summary
echo ""
echo -e "${GREEN}📊 Test Summary:${NC}"
echo "   Passed: ${PASSED_TESTS}"
echo "   Failed: ${FAILED_TESTS}"

if [[ ${FAILED_TESTS} -gt 0 ]]; then
    echo -e "${RED}❌ Smoke tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    exit 0
fi
