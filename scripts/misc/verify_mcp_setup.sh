#!/bin/bash

###############################################################################
# GitHub MCP Server - Verification Script
# سكريبت التحقق من خادم GitHub MCP
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}   $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

check_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN: $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# Verification Tests
###############################################################################

print_header "🔍 GitHub MCP Server Verification"
echo "Starting comprehensive verification..."
echo ""

###############################################################################
# Test 1: Docker Installation
###############################################################################

print_info "Test 1: Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    check_pass "Docker is installed (version: $DOCKER_VERSION)"
else
    check_fail "Docker is not installed"
    echo "       Install from: https://docs.docker.com/get-docker/"
fi

###############################################################################
# Test 2: Docker Daemon Running
###############################################################################

print_info "Test 2: Checking Docker daemon..."
if docker info &> /dev/null; then
    check_pass "Docker daemon is running"
else
    check_fail "Docker daemon is not running"
    echo "       Start Docker and try again"
fi

###############################################################################
# Test 3: .env File Exists
###############################################################################

print_info "Test 3: Checking .env file..."
if [ -f .env ]; then
    check_pass ".env file exists"
else
    check_fail ".env file not found"
    if [ -f .env.example ]; then
        echo "       Run: cp .env.example .env"
    fi
fi

###############################################################################
# Test 4: GitHub Token in .env
###############################################################################

print_info "Test 4: Checking GitHub token configuration..."
if [ -f .env ]; then
    if grep -q "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env; then
        TOKEN_VALUE=$(grep "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
        
        if [ -z "$TOKEN_VALUE" ] || [ "$TOKEN_VALUE" == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
            check_fail "GitHub token is not configured"
            echo "       Add your token to .env file"
            echo "       Get token from: https://github.com/settings/tokens"
        elif [[ $TOKEN_VALUE =~ ^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$ ]]; then
            TOKEN_PREFIX="${TOKEN_VALUE:0:8}..."
            check_pass "GitHub token is configured ($TOKEN_PREFIX)"
        else
            check_warn "GitHub token format may be invalid"
            echo "       Token should start with 'ghp_' or 'github_pat_'"
        fi
    else
        check_fail "GITHUB_PERSONAL_ACCESS_TOKEN not found in .env"
        echo "       Add: GITHUB_PERSONAL_ACCESS_TOKEN=\"ghp_...\""
    fi
fi

###############################################################################
# Test 5: Docker Image
###############################################################################

print_info "Test 5: Checking GitHub MCP Docker image..."
if docker images | grep -q "ghcr.io/github/github-mcp-server"; then
    IMAGE_ID=$(docker images ghcr.io/github/github-mcp-server:latest --format "{{.ID}}")
    check_pass "GitHub MCP Server image exists (ID: ${IMAGE_ID:0:12})"
else
    check_warn "GitHub MCP Server image not found"
    echo "       Run: docker pull ghcr.io/github/github-mcp-server:latest"
fi

###############################################################################
# Test 6: Docker Compose Configuration
###############################################################################

print_info "Test 6: Checking docker-compose.yml..."
if [ -f docker-compose.yml ]; then
    check_pass "docker-compose.yml exists"
    
    if grep -q "github_mcp:" docker-compose.yml; then
        check_pass "GitHub MCP service is configured"
    else
        check_fail "GitHub MCP service not found in docker-compose.yml"
    fi
else
    check_fail "docker-compose.yml not found"
fi

###############################################################################
# Test 7: Container Status
###############################################################################

print_info "Test 7: Checking container status..."
if docker ps --format "{{.Names}}" | grep -q "github-mcp"; then
    CONTAINER_NAME=$(docker ps --filter "name=github-mcp" --format "{{.Names}}" | head -1)
    CONTAINER_STATUS=$(docker ps --filter "name=github-mcp" --format "{{.Status}}" | head -1)
    check_pass "Container is running: $CONTAINER_NAME ($CONTAINER_STATUS)"
    
    # Check uptime
    print_info "Test 7a: Checking container uptime..."
    if [[ $CONTAINER_STATUS =~ "Up" ]]; then
        check_pass "Container has been up: $CONTAINER_STATUS"
    else
        check_warn "Container status: $CONTAINER_STATUS"
    fi
    
    # Check environment variable
    print_info "Test 7b: Checking container environment..."
    if docker exec "$CONTAINER_NAME" env 2>/dev/null | grep -q "GITHUB_PERSONAL_ACCESS_TOKEN"; then
        check_pass "GITHUB_PERSONAL_ACCESS_TOKEN is set in container"
    else
        check_fail "GITHUB_PERSONAL_ACCESS_TOKEN not found in container"
    fi
    
else
    check_warn "GitHub MCP Server container is not running"
    echo "       Start with: docker-compose --profile mcp up -d github_mcp"
    echo "       Or run: ./quick_start_mcp.sh"
fi

###############################################################################
# Test 8: IDE Configuration Files
###############################################################################

print_info "Test 8: Checking IDE configuration files..."

# VSCode
if [ -f .vscode/mcp-settings.json ]; then
    check_pass "VSCode MCP configuration exists"
else
    check_warn "VSCode MCP configuration not found"
    echo "       Expected at: .vscode/mcp-settings.json"
fi

# Cursor
if [ -f .cursor/mcp.json ]; then
    check_pass "Cursor IDE MCP configuration exists"
else
    check_warn "Cursor IDE MCP configuration not found"
    echo "       Expected at: .cursor/mcp.json"
fi

###############################################################################
# Test 9: GitHub API Connection (if container is running)
###############################################################################

if docker ps --format "{{.Names}}" | grep -q "github-mcp"; then
    print_info "Test 9: Testing GitHub API connection..."
    
    if [ -f .env ]; then
        source .env
        
        if [ ! -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ] && [ "$GITHUB_PERSONAL_ACCESS_TOKEN" != "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
            # Test API connection
            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
                -H "Accept: application/vnd.github.v3+json" \
                https://api.github.com/user)
            
            if [ "$RESPONSE" == "200" ]; then
                # Get user info
                USER_LOGIN=$(curl -s \
                    -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
                    -H "Accept: application/vnd.github.v3+json" \
                    https://api.github.com/user | grep -o '"login": "[^"]*' | cut -d'"' -f4)
                
                check_pass "GitHub API connection successful (user: $USER_LOGIN)"
            elif [ "$RESPONSE" == "401" ]; then
                check_fail "GitHub API authentication failed (401 Unauthorized)"
                echo "       Token may be invalid or expired"
            elif [ "$RESPONSE" == "403" ]; then
                check_fail "GitHub API permission denied (403 Forbidden)"
                echo "       Token may lack required scopes"
            else
                check_warn "GitHub API returned status: $RESPONSE"
            fi
        else
            check_warn "Skipping API test - token not configured"
        fi
    fi
fi

###############################################################################
# Test 10: Documentation
###############################################################################

print_info "Test 10: Checking documentation..."

if [ -f MCP_INTEGRATION_GUIDE_AR.md ]; then
    check_pass "Full documentation exists (MCP_INTEGRATION_GUIDE_AR.md)"
else
    check_warn "Full documentation not found"
fi

if [ -f MCP_README.md ]; then
    check_pass "Quick reference exists (MCP_README.md)"
else
    check_warn "Quick reference not found"
fi

if [ -f quick_start_mcp.sh ]; then
    check_pass "Quick setup script exists (quick_start_mcp.sh)"
    
    if [ -x quick_start_mcp.sh ]; then
        check_pass "Setup script is executable"
    else
        check_warn "Setup script is not executable"
        echo "       Run: chmod +x quick_start_mcp.sh"
    fi
else
    check_warn "Quick setup script not found"
fi

###############################################################################
# Summary Report
###############################################################################

print_header "📊 Verification Summary"

echo ""
echo -e "${GREEN}✅ Passed Tests: $PASSED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "${RED}❌ Failed Tests: $FAILED${NC}"
echo ""

TOTAL=$((PASSED + FAILED + WARNINGS))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED * 100) / TOTAL ))
    echo "Success Rate: $SUCCESS_RATE%"
fi

echo ""

###############################################################################
# Final Recommendations
###############################################################################

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  CRITICAL ISSUES FOUND!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Please fix the failed tests above before using MCP Server."
    echo ""
    echo "Quick fixes:"
    echo "  1. Ensure Docker is installed and running"
    echo "  2. Create/configure .env file with GitHub token"
    echo "  3. Pull MCP Docker image: docker pull ghcr.io/github/github-mcp-server"
    echo "  4. Start MCP: docker-compose --profile mcp up -d github_mcp"
    echo ""
    echo "For detailed help, see: MCP_INTEGRATION_GUIDE_AR.md"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  WARNINGS FOUND${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Your setup has some warnings but should work."
    echo "Review the warnings above and fix them when possible."
    echo ""
    echo "Next steps:"
    echo "  1. Start MCP if not running: docker-compose --profile mcp up -d"
    echo "  2. Configure your IDE (VSCode or Cursor)"
    echo "  3. Test GitHub integration"
    echo ""
    exit 0
else
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 ALL TESTS PASSED! SETUP IS PERFECT!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Your GitHub MCP Server is fully configured and ready to use!"
    echo ""
    echo "You can now:"
    echo "  ✅ Use GitHub features in your IDE"
    echo "  ✅ Let AI assistants interact with GitHub"
    echo "  ✅ Automate GitHub workflows"
    echo ""
    echo "Documentation:"
    echo "  📖 Full Guide: MCP_INTEGRATION_GUIDE_AR.md"
    echo "  📖 Quick Ref: MCP_README.md"
    echo ""
    echo "Happy coding! 🚀"
    echo ""
    exit 0
fi
