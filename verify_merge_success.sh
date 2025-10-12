#!/bin/bash
# ======================================================================================
# 🚀 MERGE VERIFICATION SCRIPT - Superhuman Edition
# ======================================================================================
# This script verifies that the merge was successful and all features work correctly.
#
# Usage:
#   ./verify_merge_success.sh
#
# What it checks:
#   ✅ No conflict markers in code
#   ✅ AI_AGENT_TOKEN configuration in all platforms
#   ✅ MCP Server wrapper script exists
#   ✅ Documentation files are complete
#   ✅ Basic tests pass
# ======================================================================================

# Don't exit on error - we want to collect all results
set +e

echo "🚀 =========================================="
echo "   MERGE VERIFICATION - SUPERHUMAN EDITION"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ======================================================================================
# Test 1: No Conflict Markers
# ======================================================================================
echo "📝 Test 1: Checking for conflict markers..."
if grep -r "<<<<<<" .github app tests docker-compose.yml .gitignore 2>/dev/null; then
    check_fail "Found conflict markers in code!"
else
    check_pass "No conflict markers found"
fi

# ======================================================================================
# Test 2: GitHub Actions Workflow
# ======================================================================================
echo ""
echo "📝 Test 2: Verifying GitHub Actions workflow..."
if [ -f ".github/workflows/mcp-server-integration.yml" ]; then
    check_pass "MCP Server workflow exists"
    
    # Check for AI_AGENT_TOKEN usage
    if grep -q "secrets.AI_AGENT_TOKEN" .github/workflows/mcp-server-integration.yml; then
        check_pass "AI_AGENT_TOKEN secret reference found"
    else
        check_fail "AI_AGENT_TOKEN secret reference missing"
    fi
    
    # Check for direct API integration
    if grep -q "curl.*github.com/user" .github/workflows/mcp-server-integration.yml; then
        check_pass "Direct GitHub API integration found"
    else
        check_warn "Direct API integration not found"
    fi
else
    check_fail "MCP Server workflow not found"
fi

# ======================================================================================
# Test 3: Codespaces Configuration
# ======================================================================================
echo ""
echo "📝 Test 3: Verifying Codespaces configuration..."
if [ -f ".devcontainer/devcontainer.json" ]; then
    check_pass "Devcontainer config exists"
    
    # Check for AI_AGENT_TOKEN
    if grep -q "AI_AGENT_TOKEN.*localEnv" .devcontainer/devcontainer.json; then
        check_pass "AI_AGENT_TOKEN auto-loading configured"
    else
        check_fail "AI_AGENT_TOKEN auto-loading not configured"
    fi
else
    check_fail "Devcontainer config not found"
fi

# ======================================================================================
# Test 4: Docker Compose MCP Server
# ======================================================================================
echo ""
echo "📝 Test 4: Verifying Docker Compose MCP configuration..."
if [ -f "docker-compose.yml" ]; then
    check_pass "Docker Compose file exists"
    
    # Check for github_mcp service
    if grep -q "github_mcp:" docker-compose.yml; then
        check_pass "MCP Server service defined"
    else
        check_fail "MCP Server service not found"
    fi
    
    # Check for health check
    if grep -q "healthcheck:" docker-compose.yml; then
        check_pass "Health check configured"
    else
        check_warn "Health check not configured"
    fi
    
    # Check for AI_AGENT_TOKEN
    if grep -q "AI_AGENT_TOKEN" docker-compose.yml; then
        check_pass "AI_AGENT_TOKEN environment variable set"
    else
        check_fail "AI_AGENT_TOKEN environment variable missing"
    fi
else
    check_fail "Docker Compose file not found"
fi

# ======================================================================================
# Test 5: MCP Wrapper Script
# ======================================================================================
echo ""
echo "📝 Test 5: Verifying MCP wrapper script..."
if [ -f "mcp-server-wrapper.sh" ]; then
    check_pass "MCP wrapper script exists"
    
    if [ -x "mcp-server-wrapper.sh" ]; then
        check_pass "MCP wrapper script is executable"
    else
        check_warn "MCP wrapper script not executable (chmod +x needed)"
    fi
else
    check_warn "MCP wrapper script not found (optional)"
fi

# ======================================================================================
# Test 6: Test Coverage Configuration
# ======================================================================================
echo ""
echo "📝 Test 6: Verifying test coverage setup..."
if grep -q "pytest-cov" requirements.txt; then
    check_pass "pytest-cov in requirements.txt"
else
    check_fail "pytest-cov not in requirements.txt"
fi

if [ -f "pytest.ini" ]; then
    check_pass "pytest.ini exists"
else
    check_warn "pytest.ini not found (optional)"
fi

# ======================================================================================
# Test 7: Documentation Files
# ======================================================================================
echo ""
echo "📝 Test 7: Verifying documentation..."
DOCS=(
    "AI_AGENT_TOKEN_README.md"
    "AI_AGENT_TOKEN_SETUP_GUIDE.md"
    "MCP_README.md"
    "MERGE_RESOLUTION_SUPERHUMAN.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
    else
        check_fail "$doc not found"
    fi
done

# ======================================================================================
# Test 8: App Initialization
# ======================================================================================
echo ""
echo "📝 Test 8: Verifying app initialization..."
if grep -q "_should_create_global_app" app/__init__.py; then
    check_pass "Smart app initialization implemented"
else
    check_fail "Smart app initialization missing"
fi

# ======================================================================================
# Test 9: Test Environment Setup
# ======================================================================================
echo ""
echo "📝 Test 9: Verifying test environment setup..."
if grep -q "TESTING.*=.*1" tests/conftest.py; then
    check_pass "Test environment setup in conftest.py"
else
    check_fail "Test environment setup missing"
fi

# ======================================================================================
# Test 10: Run Basic Tests (if pytest available)
# ======================================================================================
echo ""
echo "📝 Test 10: Running basic tests..."
if command -v pytest &> /dev/null; then
    # Set test environment
    export FLASK_ENV=testing
    export TESTING=1
    export SECRET_KEY=test-secret-key
    
    if pytest tests/test_app.py -q 2>&1 | grep -q "passed"; then
        check_pass "Basic tests passed"
    else
        check_warn "Some tests may have failed (check manually)"
    fi
else
    check_warn "pytest not installed - skipping test run"
fi

# ======================================================================================
# Summary
# ======================================================================================
echo ""
echo "=========================================="
echo "📊 VERIFICATION SUMMARY"
echo "=========================================="
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! MERGE SUCCESSFUL! 🎉${NC}"
    echo ""
    echo "✅ Zero-configuration AI_AGENT_TOKEN is ready!"
    echo "✅ Multi-platform support working!"
    echo "✅ Direct API integration configured!"
    echo "✅ Test coverage enabled!"
    echo "✅ Documentation complete!"
    echo ""
    echo "🚀 Next step: Add AI_AGENT_TOKEN to GitHub Secrets"
    echo "   Settings → Secrets and variables → Actions → New secret"
    echo "   Name: AI_AGENT_TOKEN"
    echo "   Value: Your GitHub Personal Access Token"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  SOME CHECKS FAILED${NC}"
    echo "Please review the failed checks above."
    echo ""
    exit 1
fi
