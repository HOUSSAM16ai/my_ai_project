#!/bin/bash

###############################################################################
# GitHub MCP Server - Quick Setup Script
# مشروع CogniForge - تثبيت سريع لخادم GitHub MCP
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji support
CHECK="✅"
CROSS="❌"
ROCKET="🚀"
LOCK="🔐"
GEAR="⚙️"
WARN="⚠️"

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

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARN} $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# Main Script
###############################################################################

print_header "${ROCKET} GitHub MCP Server Setup - إعداد خادم GitHub MCP"

echo "This script will help you set up GitHub MCP Server integration."
echo "هذا السكريبت سيساعدك على إعداد تكامل خادم GitHub MCP."
echo ""

###############################################################################
# Step 1: Check Docker
###############################################################################

print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    print_error "Docker غير مثبت!"
    print_info "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
else
    print_success "Docker is installed"
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running!"
    print_error "خدمة Docker غير شغالة!"
    print_info "Please start Docker and try again."
    exit 1
else
    print_success "Docker daemon is running"
fi

###############################################################################
# Step 2: Check for existing .env file
###############################################################################

print_info "Checking for .env file..."
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"
    else
        print_error ".env.example not found!"
        exit 1
    fi
else
    print_success ".env file exists"
fi

###############################################################################
# Step 3: Check for GitHub token in .env (AI_AGENT_TOKEN or legacy)
###############################################################################

print_info "Checking for AI Agent Token..."

# Check for new AI_AGENT_TOKEN first
if grep -q "^AI_AGENT_TOKEN=" .env 2>/dev/null; then
    TOKEN_VALUE=$(grep "^AI_AGENT_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
    TOKEN_VAR_NAME="AI_AGENT_TOKEN"
elif grep -q "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env 2>/dev/null; then
    TOKEN_VALUE=$(grep "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
    TOKEN_VAR_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"
    print_warning "Using legacy GITHUB_PERSONAL_ACCESS_TOKEN"
    print_info "Consider updating to AI_AGENT_TOKEN for superhuman features"
else
    TOKEN_VALUE=""
    TOKEN_VAR_NAME="AI_AGENT_TOKEN"
fi

if [ "$TOKEN_VALUE" == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ] || [ -z "$TOKEN_VALUE" ]; then
    print_warning "AI Agent Token is not configured yet"
    TOKEN_NEEDS_SETUP=true
else
    print_success "AI Agent Token is configured"
    TOKEN_NEEDS_SETUP=false
fi

###############################################################################
# Step 4: Interactive token setup if needed
###############################################################################

if [ "$TOKEN_NEEDS_SETUP" = true ]; then
    echo ""
    print_header "${LOCK} 🚀 AI Agent Token Setup - SUPERHUMAN EDITION"
    echo ""
    echo "You need an AI Agent Token (GitHub Personal Access Token) for:"
    echo "  ${ROCKET} MCP Server Integration"
    echo "  ${ROCKET} GitHub Copilot AI Features"
    echo "  ${ROCKET} Automated CI/CD with AI"
    echo "  ${ROCKET} Intelligent Dependency Management"
    echo ""
    echo "تحتاج إلى رمز AI Agent لتفعيل المميزات الخارقة!"
    echo ""
    echo "How to get your token | كيفية الحصول على الرمز:"
    echo "  1. Visit: https://github.com/settings/tokens"
    echo "  2. Click 'Generate new token (classic)'"
    echo "  3. Select scopes | اختر الصلاحيات:"
    echo "     ${CHECK} repo (required)"
    echo "     ${CHECK} read:org"
    echo "     ${CHECK} workflow"
    echo "  4. Copy the generated token"
    echo ""

    read -p "Do you want to enter your token now? (y/n) | هل تريد إدخال الرمز الآن؟ " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        read -sp "Enter your AI Agent Token (GitHub PAT): " GITHUB_TOKEN
        echo ""

        if [ -z "$GITHUB_TOKEN" ]; then
            print_error "Token cannot be empty!"
            print_info "You can manually add it to .env file later."
        else
            # Validate token format
            if [[ $GITHUB_TOKEN =~ ^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$ ]]; then
                # Add or update AI_AGENT_TOKEN in .env
                if grep -q "^AI_AGENT_TOKEN=" .env; then
                    sed -i "s|^AI_AGENT_TOKEN=.*|AI_AGENT_TOKEN=\"${GITHUB_TOKEN}\"|" .env
                elif grep -q "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env; then
                    # Replace legacy token with new one
                    sed -i "s|^GITHUB_PERSONAL_ACCESS_TOKEN=.*|AI_AGENT_TOKEN=\"${GITHUB_TOKEN}\"|" .env
                else
                    echo "AI_AGENT_TOKEN=\"${GITHUB_TOKEN}\"" >> .env
                fi

                # Also add legacy token for backward compatibility
                if ! grep -q "^GITHUB_PERSONAL_ACCESS_TOKEN=" .env; then
                    echo "GITHUB_PERSONAL_ACCESS_TOKEN=\"\${AI_AGENT_TOKEN}\"" >> .env
                fi

                print_success "AI Agent Token added to .env file"
                print_info "Token will work in GitHub Actions, Codespaces, and Dependabot!"
            else
                print_error "Invalid token format!"
                print_warning "Token should start with 'ghp_' or 'github_pat_'"
                print_info "You can manually add it to .env file later."
            fi
        fi
    else
        print_info "Skipping token setup. You can add it manually to .env file."
        echo ""
        echo "Add these lines to .env:"
        echo "AI_AGENT_TOKEN=\"ghp_your_token_here\""
        echo "GITHUB_PERSONAL_ACCESS_TOKEN=\"\${AI_AGENT_TOKEN}\""
        echo ""
        echo "Then add to GitHub Secrets:"
        echo "  - Actions: Settings > Secrets > Actions > AI_AGENT_TOKEN"
        echo "  - Codespaces: Settings > Codespaces > Secrets > AI_AGENT_TOKEN"
        echo "  - Dependabot: Settings > Secrets > Dependabot > AI_AGENT_TOKEN"
    fi
fi

###############################################################################
# Step 5: Pull Docker Image
###############################################################################

print_header "${GEAR} Pulling GitHub MCP Server Docker Image"

print_info "Pulling ghcr.io/github/github-mcp-server:latest..."
if docker pull ghcr.io/github/github-mcp-server:latest; then
    print_success "Docker image pulled successfully"
else
    print_error "Failed to pull Docker image"
    exit 1
fi

###############################################################################
# Step 6: Check docker-compose.yml
###############################################################################

print_info "Checking docker-compose.yml configuration..."
if [ -f docker-compose.yml ]; then
    if grep -q "github_mcp:" docker-compose.yml; then
        print_success "GitHub MCP service is configured in docker-compose.yml"
    else
        print_warning "GitHub MCP service not found in docker-compose.yml"
        print_info "The service configuration should already be there."
    fi
else
    print_error "docker-compose.yml not found!"
    exit 1
fi

###############################################################################
# Step 7: Start MCP Server
###############################################################################

print_header "${ROCKET} Starting GitHub MCP Server"

echo "Choose startup method | اختر طريقة التشغيل:"
echo "  1) Start with all services (docker-compose --profile full)"
echo "  2) Start MCP only (docker-compose --profile mcp)"
echo "  3) Start manually with Docker run"
echo "  4) Skip startup (manual setup later)"
echo ""

read -p "Enter your choice (1-4): " -n 1 -r STARTUP_CHOICE
echo ""
echo ""

case $STARTUP_CHOICE in
    1)
        print_info "Starting all services..."
        docker-compose --profile full up -d
        print_success "All services started"
        ;;
    2)
        print_info "Starting MCP service only..."
        docker-compose --profile mcp up -d github_mcp
        print_success "MCP service started"
        ;;
    3)
        print_info "Starting with Docker run..."
        # Load token from .env
        if [ -f .env ]; then
            source .env
        fi

        if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
            print_error "GITHUB_PERSONAL_ACCESS_TOKEN not set in .env"
            exit 1
        fi

        docker run -d \
            --name github-mcp-server \
            --network host \
            --restart unless-stopped \
            -e GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}" \
            ghcr.io/github/github-mcp-server

        print_success "MCP container started"
        ;;
    4)
        print_info "Skipping startup. You can start manually later."
        ;;
    *)
        print_warning "Invalid choice. Skipping startup."
        ;;
esac

###############################################################################
# Step 8: Verification
###############################################################################

print_header "${CHECK} Verification - التحقق"

echo "Checking container status..."
if docker ps | grep -q github-mcp; then
    print_success "GitHub MCP Server container is running"

    echo ""
    print_info "Container details:"
    docker ps --filter "name=github-mcp" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    print_info "To view logs, run:"
    echo "  docker logs github-mcp-server"
    echo ""
    print_info "To stop the server, run:"
    echo "  docker stop github-mcp-server"

else
    print_warning "GitHub MCP Server container is not running"
    print_info "You can start it manually using one of the methods above."
fi

###############################################################################
# Step 9: IDE Configuration Check
###############################################################################

print_header "${GEAR} IDE Configuration Check"

if [ -f .vscode/mcp-settings.json ]; then
    print_success "VSCode MCP configuration exists (.vscode/mcp-settings.json)"
else
    print_warning "VSCode MCP configuration not found"
fi

if [ -f .cursor/mcp.json ]; then
    print_success "Cursor IDE MCP configuration exists (.cursor/mcp.json)"
else
    print_warning "Cursor IDE MCP configuration not found"
fi

###############################################################################
# Final Summary
###############################################################################

print_header "${ROCKET} Setup Complete! - اكتمل الإعداد"

echo ""
echo "🎉 GitHub MCP Server setup is complete!"
echo "🎉 اكتمل إعداد خادم GitHub MCP!"
echo ""
echo "Next steps | الخطوات التالية:"
echo ""
echo "1. ${CHECK} Verify your GitHub token in .env"
echo "   تحقق من رمز GitHub في ملف .env"
echo ""
echo "2. ${CHECK} Review MCP configuration:"
echo "   راجع تكوين MCP:"
echo "   - .vscode/mcp-settings.json (for VSCode)"
echo "   - .cursor/mcp.json (for Cursor IDE)"
echo ""
echo "3. ${CHECK} Read the full documentation:"
echo "   اقرأ الوثائق الكاملة:"
echo "   - MCP_INTEGRATION_GUIDE_AR.md"
echo ""
echo "4. ${CHECK} Test the connection:"
echo "   اختبر الاتصال:"
echo "   - Run: docker logs github-mcp-server"
echo "   - Open your IDE and check MCP status"
echo ""

print_success "Happy coding! - برمجة سعيدة! 🚀"
echo ""
