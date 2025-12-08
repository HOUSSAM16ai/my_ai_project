#!/bin/bash
# ======================================================================================
# GitLab CI/CD Health Check Script
# ======================================================================================
# Verify deployment health after deployment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-development}"
URL="${2:-}"
MAX_RETRIES=30
RETRY_INTERVAL=10

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
        *)
            echo -e "${RED}❌ Unknown environment: ${ENVIRONMENT}${NC}"
            exit 1
            ;;
    esac
fi

echo -e "${GREEN}🏥 Starting health checks for ${ENVIRONMENT}${NC}"
echo "   URL: ${URL}"
echo "   Max retries: ${MAX_RETRIES}"
echo ""

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=$2
    
    echo -e "${YELLOW}🔍 Checking ${endpoint}...${NC}"
    
    for i in $(seq 1 ${MAX_RETRIES}); do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}${endpoint}" || echo "000")
        
        if [[ "${HTTP_CODE}" == "${expected_status}" ]]; then
            echo -e "${GREEN}✅ ${endpoint} returned ${HTTP_CODE}${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt ${i}/${MAX_RETRIES}: ${endpoint} returned ${HTTP_CODE}, retrying...${NC}"
        sleep ${RETRY_INTERVAL}
    done
    
    echo -e "${RED}❌ ${endpoint} failed after ${MAX_RETRIES} attempts${NC}"
    return 1
}

# Check health endpoint
if ! check_endpoint "/health" "200"; then
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

# Check readiness endpoint
if ! check_endpoint "/health/ready" "200"; then
    echo -e "${RED}❌ Readiness check failed${NC}"
    exit 1
fi

# Check metrics endpoint
if ! check_endpoint "/metrics" "200"; then
    echo -e "${YELLOW}⚠️  Metrics endpoint not available (non-critical)${NC}"
fi

# Performance check
echo -e "${YELLOW}⚡ Checking response time...${NC}"
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "${URL}/health")
RESPONSE_MS=$(echo "${RESPONSE_TIME} * 1000" | bc)

echo "   Response time: ${RESPONSE_MS}ms"

if (( $(echo "${RESPONSE_TIME} > 2.0" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Response time is high (>${RESPONSE_MS}ms)${NC}"
else
    echo -e "${GREEN}✅ Response time is good${NC}"
fi

# Check SSL certificate
echo -e "${YELLOW}🔒 Checking SSL certificate...${NC}"
if echo | openssl s_client -servername "${URL#https://}" -connect "${URL#https://}:443" 2>/dev/null | openssl x509 -noout -dates; then
    echo -e "${GREEN}✅ SSL certificate is valid${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify SSL certificate${NC}"
fi

echo ""
echo -e "${GREEN}✅ All health checks passed!${NC}"
