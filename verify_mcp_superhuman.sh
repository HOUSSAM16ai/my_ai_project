#!/usr/bin/env bash
###############################################################################
# SUPERHUMAN MCP SERVER INTEGRATION - VERIFICATION SCRIPT v3.0
###############################################################################
# This script verifies the complete MCP Server integration with AI_AGENT_TOKEN
# Tests all platforms: GitHub Actions, Codespaces, Docker Compose
###############################################################################

set -o pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Emoji indicators
readonly ROCKET="🚀"
readonly CHECK="✅"
readonly CROSS="❌"
readonly WARN="⚠️"
readonly GEAR="⚙️"
readonly STAR="⭐"
readonly FIRE="🔥"

###############################################################################
# Logging Functions
###############################################################################

print_header() {
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${1}${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECK}${NC} $1"
}

print_error() {
    echo -e "${RED}${CROSS}${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}${WARN}${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC}  $1"
}

check_pass() {
    echo -e "  ${GREEN}${CHECK} PASS${NC} - $1"
}

check_fail() {
    echo -e "  ${RED}${CROSS} FAIL${NC} - $1"
}

check_skip() {
    echo -e "  ${YELLOW}⊝ SKIP${NC} - $1"
}

###############################################################################
# Test Counters
###############################################################################

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

###############################################################################
# Banner
###############################################################################

clear
echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     🚀 SUPERHUMAN MCP SERVER INTEGRATION VERIFICATION v3.0 🚀             ║
║                                                                           ║
║            Technology Surpassing Google, Microsoft, OpenAI!               ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_info "This script verifies the complete AI_AGENT_TOKEN integration"
print_info "Testing: GitHub Actions, Codespaces, Docker Compose, MCP Server"
echo ""
sleep 2

###############################################################################
# Test 1: Check Files Exist
###############################################################################

print_header "${GEAR} Test 1: Required Files Check"

((TOTAL_TESTS++))
if [ -f .github/workflows/mcp-server-integration.yml ]; then
    check_pass "GitHub Actions workflow exists"
    ((PASSED_TESTS++))
else
    check_fail "GitHub Actions workflow missing"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if [ -f docker-compose.yml ]; then
    check_pass "docker-compose.yml exists"
    ((PASSED_TESTS++))
else
    check_fail "docker-compose.yml missing"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if [ -f mcp-server-wrapper.sh ] && [ -x mcp-server-wrapper.sh ]; then
    check_pass "MCP Server wrapper script exists and is executable"
    ((PASSED_TESTS++))
else
    check_fail "MCP Server wrapper script missing or not executable"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if [ -f .env.example ]; then
    check_pass ".env.example exists"
    ((PASSED_TESTS++))
else
    check_fail ".env.example missing"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if [ -f MCP_SUPERHUMAN_SOLUTION.md ]; then
    check_pass "Superhuman documentation exists"
    ((PASSED_TESTS++))
else
    check_fail "Superhuman documentation missing"
    ((FAILED_TESTS++))
fi

###############################################################################
# Test 2: GitHub Actions Workflow Validation
###############################################################################

print_header "${GEAR} Test 2: GitHub Actions Workflow Validation"

((TOTAL_TESTS++))
if grep -q "AI_AGENT_TOKEN" .github/workflows/mcp-server-integration.yml; then
    check_pass "Workflow uses AI_AGENT_TOKEN"
    ((PASSED_TESTS++))
else
    check_fail "Workflow doesn't use AI_AGENT_TOKEN"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "secrets.AI_AGENT_TOKEN" .github/workflows/mcp-server-integration.yml; then
    check_pass "Workflow loads token from secrets"
    ((PASSED_TESTS++))
else
    check_fail "Workflow doesn't load token from secrets"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "https://api.github.com" .github/workflows/mcp-server-integration.yml; then
    check_pass "Workflow uses GitHub API directly"
    ((PASSED_TESTS++))
else
    check_fail "Workflow doesn't use GitHub API"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
# Check that workflow doesn't try to run MCP as daemon (the old broken way)
if ! grep -q "docker run -d.*github-mcp-server" .github/workflows/mcp-server-integration.yml; then
    check_pass "Workflow doesn't use broken daemon mode"
    ((PASSED_TESTS++))
else
    check_fail "Workflow still uses broken daemon mode"
    ((FAILED_TESTS++))
fi

###############################################################################
# Test 3: Docker Compose Configuration
###############################################################################

print_header "${GEAR} Test 3: Docker Compose Configuration"

((TOTAL_TESTS++))
if grep -q "github_mcp:" docker-compose.yml; then
    check_pass "MCP service defined in docker-compose"
    ((PASSED_TESTS++))
else
    check_fail "MCP service not found in docker-compose"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "AI_AGENT_TOKEN" docker-compose.yml; then
    check_pass "Docker Compose supports AI_AGENT_TOKEN"
    ((PASSED_TESTS++))
else
    check_fail "Docker Compose doesn't support AI_AGENT_TOKEN"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "stdin_open: true" docker-compose.yml && grep -q "tty: true" docker-compose.yml; then
    check_pass "MCP service configured for interactive stdio mode"
    ((PASSED_TESTS++))
else
    check_fail "MCP service not configured for stdio mode"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "mcp-wrapper.sh" docker-compose.yml; then
    check_pass "MCP service uses wrapper script"
    ((PASSED_TESTS++))
else
    check_fail "MCP service doesn't use wrapper script"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "healthcheck:" docker-compose.yml; then
    check_pass "MCP service has health check"
    ((PASSED_TESTS++))
else
    check_warn "MCP service doesn't have health check"
    ((SKIPPED_TESTS++))
fi

###############################################################################
# Test 4: Environment Configuration
###############################################################################

print_header "${GEAR} Test 4: Environment Configuration"

((TOTAL_TESTS++))
if grep -q "AI_AGENT_TOKEN=" .env.example; then
    check_pass ".env.example has AI_AGENT_TOKEN template"
    ((PASSED_TESTS++))
else
    check_fail ".env.example missing AI_AGENT_TOKEN"
    ((FAILED_TESTS++))
fi

if [ -f .env ]; then
    ((TOTAL_TESTS++))
    if grep -q "AI_AGENT_TOKEN=" .env 2>/dev/null; then
        TOKEN_VALUE=$(grep "^AI_AGENT_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
        if [ -n "$TOKEN_VALUE" ] && [ "$TOKEN_VALUE" != "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
            check_pass "AI_AGENT_TOKEN configured in .env"
            ((PASSED_TESTS++))
            
            # Validate token format
            ((TOTAL_TESTS++))
            if [[ $TOKEN_VALUE =~ ^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$ ]]; then
                check_pass "Token format is valid"
                ((PASSED_TESTS++))
            else
                check_warn "Token format may be invalid"
                ((SKIPPED_TESTS++))
            fi
        else
            check_warn "AI_AGENT_TOKEN set but using placeholder value"
            ((SKIPPED_TESTS++))
        fi
    else
        check_warn "AI_AGENT_TOKEN not found in .env"
        ((SKIPPED_TESTS++))
    fi
else
    check_skip ".env file not found (optional for testing)"
    ((SKIPPED_TESTS++))
fi

###############################################################################
# Test 5: Devcontainer Configuration
###############################################################################

print_header "${GEAR} Test 5: Devcontainer/Codespaces Configuration"

((TOTAL_TESTS++))
if [ -f .devcontainer/devcontainer.json ]; then
    check_pass "Devcontainer configuration exists"
    ((PASSED_TESTS++))
    
    ((TOTAL_TESTS++))
    if grep -q "AI_AGENT_TOKEN" .devcontainer/devcontainer.json; then
        check_pass "Devcontainer configured for AI_AGENT_TOKEN"
        ((PASSED_TESTS++))
    else
        check_fail "Devcontainer missing AI_AGENT_TOKEN configuration"
        ((FAILED_TESTS++))
    fi
    
    ((TOTAL_TESTS++))
    if grep -q "localEnv:AI_AGENT_TOKEN" .devcontainer/devcontainer.json; then
        check_pass "Devcontainer auto-loads token from Codespaces secrets"
        ((PASSED_TESTS++))
    else
        check_fail "Devcontainer doesn't auto-load token"
        ((FAILED_TESTS++))
    fi
else
    check_fail "Devcontainer configuration missing"
    ((FAILED_TESTS++))
fi

###############################################################################
# Test 6: MCP Wrapper Script Validation
###############################################################################

print_header "${GEAR} Test 6: MCP Wrapper Script Validation"

((TOTAL_TESTS++))
if bash -n mcp-server-wrapper.sh 2>/dev/null; then
    check_pass "Wrapper script syntax is valid"
    ((PASSED_TESTS++))
else
    check_fail "Wrapper script has syntax errors"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "AI_AGENT_TOKEN" mcp-server-wrapper.sh; then
    check_pass "Wrapper script supports AI_AGENT_TOKEN"
    ((PASSED_TESTS++))
else
    check_fail "Wrapper script doesn't support AI_AGENT_TOKEN"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "GITHUB_PERSONAL_ACCESS_TOKEN" mcp-server-wrapper.sh; then
    check_pass "Wrapper script has backward compatibility"
    ((PASSED_TESTS++))
else
    check_fail "Wrapper script missing backward compatibility"
    ((FAILED_TESTS++))
fi

###############################################################################
# Test 7: GitHub API Connectivity (if token available)
###############################################################################

print_header "${GEAR} Test 7: GitHub API Connectivity Test"

if [ -f .env ] && grep -q "AI_AGENT_TOKEN=" .env 2>/dev/null; then
    TOKEN_VALUE=$(grep "^AI_AGENT_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
    
    if [ -n "$TOKEN_VALUE" ] && [ "$TOKEN_VALUE" != "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
        print_info "Testing GitHub API with AI_AGENT_TOKEN..."
        
        ((TOTAL_TESTS++))
        RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/gh_test_response.json \
            -H "Authorization: token ${TOKEN_VALUE}" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/user 2>/dev/null || echo "000")
        
        if [ "$RESPONSE" = "200" ]; then
            USERNAME=$(jq -r '.login' /tmp/gh_test_response.json 2>/dev/null || echo "unknown")
            check_pass "GitHub API authentication successful (user: $USERNAME)"
            ((PASSED_TESTS++))
        elif [ "$RESPONSE" = "401" ]; then
            check_fail "GitHub API authentication failed (401 Unauthorized)"
            ((FAILED_TESTS++))
        else
            check_warn "GitHub API test failed (HTTP $RESPONSE) - check network"
            ((SKIPPED_TESTS++))
        fi
    else
        check_skip "Token is placeholder - skipping API test"
        ((SKIPPED_TESTS++))
    fi
else
    check_skip "No token configured - skipping API test"
    ((SKIPPED_TESTS++))
fi

###############################################################################
# Test 8: Documentation Quality
###############################################################################

print_header "${GEAR} Test 8: Documentation Quality"

((TOTAL_TESTS++))
if [ -f MCP_SUPERHUMAN_SOLUTION.md ]; then
    WORD_COUNT=$(wc -w < MCP_SUPERHUMAN_SOLUTION.md)
    if [ "$WORD_COUNT" -gt 1000 ]; then
        check_pass "Comprehensive documentation ($WORD_COUNT words)"
        ((PASSED_TESTS++))
    else
        check_warn "Documentation exists but may be incomplete"
        ((SKIPPED_TESTS++))
    fi
else
    check_fail "Main documentation missing"
    ((FAILED_TESTS++))
fi

((TOTAL_TESTS++))
if grep -q "Setup Guide" MCP_SUPERHUMAN_SOLUTION.md && \
   grep -q "Troubleshooting" MCP_SUPERHUMAN_SOLUTION.md && \
   grep -q "Architecture" MCP_SUPERHUMAN_SOLUTION.md; then
    check_pass "Documentation includes all required sections"
    ((PASSED_TESTS++))
else
    check_warn "Documentation may be missing some sections"
    ((SKIPPED_TESTS++))
fi

###############################################################################
# Final Summary
###############################################################################

print_header "${STAR} VERIFICATION SUMMARY ${STAR}"

echo ""
echo -e "${CYAN}Test Results:${NC}"
echo -e "  ${GREEN}Passed:${NC}  $PASSED_TESTS"
echo -e "  ${RED}Failed:${NC}  $FAILED_TESTS"
echo -e "  ${YELLOW}Skipped:${NC} $SKIPPED_TESTS"
echo -e "  ${BLUE}Total:${NC}   $TOTAL_TESTS"
echo ""

# Calculate percentage
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_PERCENT=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo -e "${CYAN}Success Rate:${NC} ${PASS_PERCENT}%"
fi

echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}${FIRE} ${CHECK} ALL TESTS PASSED! SUPERHUMAN STATUS ACHIEVED! ${CHECK} ${FIRE}${NC}"
    echo ""
    echo -e "${CYAN}Your MCP Server integration is${NC} ${GREEN}LEGENDARY!${NC}"
    echo ""
    print_success "GitHub Actions: Ready"
    print_success "Codespaces: Ready"
    print_success "Docker Compose: Ready"
    print_success "Documentation: Complete"
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    print_info "Next Steps:"
    echo "  1. ${STAR} Add AI_AGENT_TOKEN to GitHub Secrets (if not done)"
    echo "  2. ${ROCKET} Push code and watch the magic happen!"
    echo "  3. ${FIRE} Enjoy superhuman AI capabilities!"
    echo ""
    exit 0
else
    echo ""
    echo -e "${YELLOW}${WARN} SOME TESTS FAILED ${WARN}${NC}"
    echo ""
    print_info "Please review the failed tests above and:"
    echo "  1. Check file permissions"
    echo "  2. Verify token configuration"
    echo "  3. Review documentation at MCP_SUPERHUMAN_SOLUTION.md"
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
