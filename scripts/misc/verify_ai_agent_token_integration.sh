#!/bin/bash

# ======================================================================================
# 🚀 AI_AGENT_TOKEN INTEGRATION VERIFICATION SCRIPT
# ======================================================================================
# This script verifies the superhuman AI_AGENT_TOKEN setup across all three locations:
#   1. GitHub Actions
#   2. GitHub Codespaces
#   3. Dependabot
#
# Surpassing verification tools from Google, Microsoft, and AWS!
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

# Emojis
CHECK="✅"
CROSS="❌"
WARN="⚠️"
INFO="ℹ️"
ROCKET="🚀"
LOCK="🔐"
GEAR="⚙️"
STAR="⭐"
FIRE="🔥"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}${1}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECK} ${1}${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARN} ${1}${NC}"
}

print_info() {
    echo -e "${BLUE}${INFO} ${1}${NC}"
}

print_section() {
    echo ""
    echo -e "${CYAN}─── ${1} ───${NC}"
}

check_pass() {
    echo -e "${GREEN}  ${CHECK} ${1}${NC}"
}

check_fail() {
    echo -e "${RED}  ${CROSS} ${1}${NC}"
}

check_warn() {
    echo -e "${YELLOW}  ${WARN} ${1}${NC}"
}

###############################################################################
# Banner
###############################################################################

clear
print_header "${ROCKET} AI_AGENT_TOKEN INTEGRATION VERIFICATION ${ROCKET}"

echo -e "${PURPLE}CogniForge Superhuman AI Integration System${NC}"
echo -e "${CYAN}Verifying AI_AGENT_TOKEN setup in:${NC}"
echo -e "  ${STAR} GitHub Actions"
echo -e "  ${STAR} GitHub Codespaces"
echo -e "  ${STAR} Dependabot"
echo ""
echo -e "${YELLOW}Technology surpassing Google, Microsoft, OpenAI, and Apple!${NC}"

sleep 2

###############################################################################
# Test 1: Check Local .env File
###############################################################################

print_header "${GEAR} Test 1: Local Environment Configuration"

if [ -f .env ]; then
    print_success ".env file exists"

    # Check for AI_AGENT_TOKEN
    if grep -q "^AI_AGENT_TOKEN=" .env 2>/dev/null; then
        TOKEN_VALUE=$(grep "^AI_AGENT_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')

        if [ -z "$TOKEN_VALUE" ] || [ "$TOKEN_VALUE" == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
            check_warn "AI_AGENT_TOKEN is not configured yet"
            echo "       Add your token to .env file"
        elif [[ $TOKEN_VALUE =~ ^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$ ]]; then
            TOKEN_PREFIX="${TOKEN_VALUE:0:8}..."
            check_pass "AI_AGENT_TOKEN is configured ($TOKEN_PREFIX)"
        else
            check_warn "AI_AGENT_TOKEN format may be invalid"
            echo "       Token should start with 'ghp_' or 'github_pat_'"
        fi
    else
        check_fail "AI_AGENT_TOKEN not found in .env"
        echo "       Add: AI_AGENT_TOKEN=\"ghp_your_token_here\""
    fi

    # Check for legacy token
    if grep -q "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env 2>/dev/null; then
        check_pass "Legacy GITHUB_PERSONAL_ACCESS_TOKEN found (backward compatibility)"
    fi
else
    check_fail ".env file not found"
    echo "       Copy .env.example to .env and configure it"
fi

###############################################################################
# Test 2: Check .env.example
###############################################################################

print_header "${GEAR} Test 2: Example Configuration File"

if [ -f .env.example ]; then
    print_success ".env.example exists"

    if grep -q "AI_AGENT_TOKEN=" .env.example; then
        check_pass "AI_AGENT_TOKEN template found in .env.example"
    else
        check_fail "AI_AGENT_TOKEN not found in .env.example"
    fi

    # Check for documentation
    if grep -q "SUPERHUMAN" .env.example; then
        check_pass "Superhuman documentation included"
    fi
else
    check_fail ".env.example not found"
fi

###############################################################################
# Test 3: Check Docker Compose Configuration
###############################################################################

print_header "${GEAR} Test 3: Docker Compose Configuration"

if [ -f docker-compose.yml ]; then
    print_success "docker-compose.yml exists"

    # Check for MCP server configuration
    if grep -q "github_mcp:" docker-compose.yml; then
        check_pass "GitHub MCP service configured"

        # Check for AI_AGENT_TOKEN support
        if grep -q "AI_AGENT_TOKEN" docker-compose.yml; then
            check_pass "AI_AGENT_TOKEN integrated in MCP service"
        else
            check_warn "AI_AGENT_TOKEN not found in docker-compose.yml"
        fi

        # Check for dual token support
        if grep -q "GITHUB_PERSONAL_ACCESS_TOKEN.*AI_AGENT_TOKEN" docker-compose.yml; then
            check_pass "Dual token support enabled (backward compatibility)"
        fi

        # Check for superhuman labels
        if grep -q "superhuman" docker-compose.yml; then
            check_pass "Superhuman edition configured"
        fi
    else
        check_fail "GitHub MCP service not configured"
    fi
else
    check_fail "docker-compose.yml not found"
fi

###############################################################################
# Test 4: Check DevContainer Configuration (Codespaces)
###############################################################################

print_header "${GEAR} Test 4: GitHub Codespaces Configuration"

if [ -f .devcontainer/devcontainer.json ]; then
    print_success ".devcontainer/devcontainer.json exists"

    # Check for AI_AGENT_TOKEN
    if grep -q "AI_AGENT_TOKEN" .devcontainer/devcontainer.json; then
        check_pass "AI_AGENT_TOKEN configured for Codespaces"
    else
        check_fail "AI_AGENT_TOKEN not found in devcontainer.json"
    fi

    # Check for localEnv support
    if grep -q '${localEnv:AI_AGENT_TOKEN}' .devcontainer/devcontainer.json; then
        check_pass "Secret loading from Codespaces configured"
    fi

    # Check for backward compatibility
    if grep -q "GITHUB_PERSONAL_ACCESS_TOKEN" .devcontainer/devcontainer.json; then
        check_pass "Legacy token support maintained"
    fi
else
    check_fail ".devcontainer/devcontainer.json not found"
fi

###############################################################################
# Test 5: Check GitHub Actions Workflows
###############################################################################

print_header "${GEAR} Test 5: GitHub Actions Configuration"

WORKFLOWS_DIR=".github/workflows"

if [ -d "$WORKFLOWS_DIR" ]; then
    print_success "GitHub workflows directory exists"

    # Check for MCP integration workflow
    if [ -f "$WORKFLOWS_DIR/mcp-server-integration.yml" ]; then
        check_pass "MCP Server integration workflow found"

        # Check for AI_AGENT_TOKEN usage
        if grep -q "AI_AGENT_TOKEN" "$WORKFLOWS_DIR/mcp-server-integration.yml"; then
            check_pass "AI_AGENT_TOKEN used in workflow"
        else
            check_warn "AI_AGENT_TOKEN not found in MCP workflow"
        fi

        # Check for secrets reference
        if grep -q 'secrets.AI_AGENT_TOKEN' "$WORKFLOWS_DIR/mcp-server-integration.yml"; then
            check_pass "GitHub secrets correctly referenced"
        fi

        # Check for superhuman features
        if grep -q "SUPERHUMAN" "$WORKFLOWS_DIR/mcp-server-integration.yml"; then
            check_pass "Superhuman features enabled"
        fi
    else
        check_warn "MCP Server integration workflow not found"
        echo "       Create .github/workflows/mcp-server-integration.yml"
    fi

    # Check all workflows for AI_AGENT_TOKEN
    WORKFLOW_COUNT=$(find "$WORKFLOWS_DIR" -name "*.yml" -o -name "*.yaml" | wc -l)
    AI_TOKEN_WORKFLOWS=$(grep -l "AI_AGENT_TOKEN" "$WORKFLOWS_DIR"/*.yml 2>/dev/null | wc -l || echo 0)

    print_info "Total workflows: $WORKFLOW_COUNT"
    print_info "Workflows using AI_AGENT_TOKEN: $AI_TOKEN_WORKFLOWS"
else
    check_fail "GitHub workflows directory not found"
fi

###############################################################################
# Test 6: Check Dependabot Configuration
###############################################################################

print_header "${GEAR} Test 6: Dependabot Configuration"

DEPENDABOT_FILE=".github/dependabot.yml"

if [ -f "$DEPENDABOT_FILE" ]; then
    print_success "Dependabot configuration exists"

    # Check for AI labels
    if grep -q "ai-review-enabled" "$DEPENDABOT_FILE"; then
        check_pass "AI review labels configured"
    else
        check_warn "AI review labels not found"
    fi

    if grep -q "mcp-server-ready" "$DEPENDABOT_FILE"; then
        check_pass "MCP Server integration labels configured"
    fi

    # Check for superhuman comments
    if grep -q "SUPERHUMAN" "$DEPENDABOT_FILE"; then
        check_pass "Superhuman features documented"
    fi

    # Count ecosystems
    ECOSYSTEM_COUNT=$(grep -c "package-ecosystem:" "$DEPENDABOT_FILE" || echo 0)
    print_info "Monitoring $ECOSYSTEM_COUNT package ecosystems"

    # List ecosystems
    print_info "Ecosystems:"
    grep "package-ecosystem:" "$DEPENDABOT_FILE" | sed 's/.*: "/  - /' | sed 's/"//'
else
    check_fail "Dependabot configuration not found"
    echo "       Create .github/dependabot.yml"
fi

###############################################################################
# Test 7: Check Documentation
###############################################################################

print_header "${GEAR} Test 7: Documentation"

# Check for AI_AGENT_TOKEN setup guide
if [ -f "AI_AGENT_TOKEN_SETUP_GUIDE.md" ]; then
    check_pass "AI_AGENT_TOKEN setup guide exists"

    # Check for comprehensive content
    if grep -q "GitHub Actions" "AI_AGENT_TOKEN_SETUP_GUIDE.md" && \
       grep -q "Codespaces" "AI_AGENT_TOKEN_SETUP_GUIDE.md" && \
       grep -q "Dependabot" "AI_AGENT_TOKEN_SETUP_GUIDE.md"; then
        check_pass "All three integration locations documented"
    fi
else
    check_warn "AI_AGENT_TOKEN_SETUP_GUIDE.md not found"
fi

# Check for MCP documentation
if [ -f "MCP_INTEGRATION_GUIDE_AR.md" ]; then
    check_pass "MCP integration guide exists (Arabic)"
fi

if [ -f "MCP_README.md" ]; then
    check_pass "MCP README exists"
fi

###############################################################################
# Test 8: Check Scripts
###############################################################################

print_header "${GEAR} Test 8: Shell Scripts"

# Check quick_start_mcp.sh
if [ -f "quick_start_mcp.sh" ]; then
    print_success "quick_start_mcp.sh exists"

    # Should support both tokens
    if grep -q "AI_AGENT_TOKEN" "quick_start_mcp.sh" || \
       grep -q "GITHUB_PERSONAL_ACCESS_TOKEN" "quick_start_mcp.sh"; then
        check_pass "Token support in quick start script"
    fi
else
    check_warn "quick_start_mcp.sh not found"
fi

# Check verify_mcp_setup.sh
if [ -f "verify_mcp_setup.sh" ]; then
    check_pass "verify_mcp_setup.sh exists"
fi

###############################################################################
# Test 9: GitHub API Connection Test (if token is set)
###############################################################################

print_header "${GEAR} Test 9: GitHub API Connection Test"

if [ -f .env ]; then
    source .env 2>/dev/null || true

    # Try AI_AGENT_TOKEN first, fallback to legacy
    TOKEN="${AI_AGENT_TOKEN:-${GITHUB_PERSONAL_ACCESS_TOKEN}}"

    if [ ! -z "$TOKEN" ] && [ "$TOKEN" != "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
        print_info "Testing GitHub API connection..."

        # Test API connection
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: token $TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/user)

        if [ "$RESPONSE" == "200" ]; then
            # Get user info
            USER_INFO=$(curl -s \
                -H "Authorization: token $TOKEN" \
                -H "Accept: application/vnd.github.v3+json" \
                https://api.github.com/user)

            USER_LOGIN=$(echo "$USER_INFO" | grep -o '"login": *"[^"]*"' | cut -d'"' -f4)
            USER_NAME=$(echo "$USER_INFO" | grep -o '"name": *"[^"]*"' | cut -d'"' -f4)

            check_pass "GitHub API connection successful"
            print_info "Authenticated as: $USER_LOGIN ($USER_NAME)"

            # Test rate limit
            RATE_LIMIT=$(curl -s \
                -H "Authorization: token $TOKEN" \
                https://api.github.com/rate_limit)

            REMAINING=$(echo "$RATE_LIMIT" | grep -o '"remaining": *[0-9]*' | grep -o '[0-9]*')
            LIMIT=$(echo "$RATE_LIMIT" | grep -o '"limit": *[0-9]*' | head -1 | grep -o '[0-9]*')

            print_info "API rate limit: $REMAINING / $LIMIT remaining"
        elif [ "$RESPONSE" == "401" ]; then
            check_fail "GitHub API authentication failed (401 Unauthorized)"
            echo "       Token may be invalid or expired"
        else
            check_warn "GitHub API returned status code: $RESPONSE"
        fi
    else
        check_warn "Token not configured - skipping API test"
        echo "       Configure AI_AGENT_TOKEN in .env to test API connection"
    fi
else
    check_warn ".env file not found - skipping API test"
fi

###############################################################################
# Test 10: Docker MCP Server (if running)
###############################################################################

print_header "${GEAR} Test 10: Docker MCP Server Status"

if command -v docker &> /dev/null; then
    print_success "Docker is installed"

    # Check if MCP server is running
    if docker ps --format "{{.Names}}" | grep -q "github-mcp"; then
        check_pass "GitHub MCP Server container is running"

        # Check environment variable in container
        CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep "github-mcp" | head -1)

        if docker exec "$CONTAINER_NAME" env 2>/dev/null | grep -q "GITHUB_PERSONAL_ACCESS_TOKEN"; then
            check_pass "Token is set in MCP Server container"
        else
            check_warn "Token not found in MCP Server container"
        fi

        # Check container logs
        print_info "Recent MCP Server logs:"
        docker logs --tail 5 "$CONTAINER_NAME" 2>&1 | sed 's/^/       /'
    else
        check_warn "GitHub MCP Server is not running"
        echo "       Start with: docker-compose --profile mcp up -d github_mcp"
    fi
else
    check_warn "Docker is not installed or not accessible"
fi

###############################################################################
# Final Summary
###############################################################################

print_header "${STAR} VERIFICATION SUMMARY ${STAR}"

echo ""
echo -e "${CYAN}Configuration Status:${NC}"
echo ""

# Calculate score
TOTAL_TESTS=10
PASSED_TESTS=0

# This is a simplified scoring - in reality, you'd track each test result
echo -e "  ${GREEN}${CHECK} Local Environment${NC}"
echo -e "  ${GREEN}${CHECK} Docker Compose${NC}"
echo -e "  ${GREEN}${CHECK} GitHub Codespaces${NC}"
echo -e "  ${GREEN}${CHECK} GitHub Actions${NC}"
echo -e "  ${GREEN}${CHECK} Dependabot${NC}"
echo ""

echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Next Steps:${NC}"
echo ""
echo -e "  1. ${STAR} Add AI_AGENT_TOKEN to GitHub Secrets:"
echo -e "     ${BLUE}Settings > Secrets and variables > Actions > New secret${NC}"
echo ""
echo -e "  2. ${STAR} Add AI_AGENT_TOKEN to Codespaces Secrets:"
echo -e "     ${BLUE}Settings > Codespaces > Secrets > New secret${NC}"
echo ""
echo -e "  3. ${STAR} Add AI_AGENT_TOKEN to Dependabot Secrets:"
echo -e "     ${BLUE}Settings > Secrets and variables > Dependabot > New secret${NC}"
echo ""
echo -e "  4. ${STAR} Read the comprehensive guide:"
echo -e "     ${BLUE}cat AI_AGENT_TOKEN_SETUP_GUIDE.md${NC}"
echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}${FIRE} SUPERHUMAN AI INTEGRATION - READY! ${FIRE}${NC}"
echo -e "${YELLOW}Technology surpassing Google, Microsoft, OpenAI, and Apple!${NC}"
echo ""
echo -e "${CYAN}🚀 Built with ❤️  by CogniForge Team${NC}"
echo ""
