#!/bin/bash
# ======================================================================================
# SUPERHUMAN STREAMING SETUP SCRIPT
# ======================================================================================
# Quick setup script for enabling/disabling advanced streaming features
#
# Usage:
#   ./setup-superhuman-streaming.sh enable    # Enable all features
#   ./setup-superhuman-streaming.sh disable   # Disable all features
#   ./setup-superhuman-streaming.sh status    # Show current status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
fi

# Function to set environment variable
set_env() {
    local key=$1
    local value=$2

    if grep -q "^${key}=" .env; then
        # Update existing
        sed -i.bak "s|^${key}=.*|${key}=${value}|g" .env
    else
        # Add new
        echo "${key}=${value}" >> .env
    fi
}

# Function to get environment variable
get_env() {
    local key=$1
    grep "^${key}=" .env 2>/dev/null | cut -d '=' -f2 || echo "not set"
}

# Function to show status
show_status() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}📊 Superhuman Streaming Status${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "Mock LLM (Dev Mode):        $(get_env ALLOW_MOCK_LLM)"
    echo -e "Hybrid Streaming:           $(get_env ENABLE_HYBRID_STREAMING)"
    echo -e "Intelligent Routing:        $(get_env ENABLE_INTELLIGENT_ROUTING)"
    echo -e "Daily Budget:               \$$(get_env LLM_DAILY_BUDGET)"
    echo ""

    echo -e "${BLUE}Model Tier Configuration:${NC}"
    echo -e "  NANO:   $(get_env NANO_MODEL)"
    echo -e "  FAST:   $(get_env FAST_MODEL)"
    echo -e "  SMART:  $(get_env SMART_MODEL)"
    echo -e "  GENIUS: $(get_env GENIUS_MODEL)"
    echo ""
}

# Function to enable features
enable_features() {
    echo -e "${GREEN}🚀 Enabling Superhuman Streaming Features...${NC}"

    # Core streaming config
    set_env "ALLOW_MOCK_LLM" "false"
    set_env "ENABLE_HYBRID_STREAMING" "true"
    set_env "ENABLE_INTELLIGENT_ROUTING" "true"

    # Ensure model configs exist
    if [ "$(get_env NANO_MODEL)" = "not set" ]; then
        set_env "NANO_MODEL" "openai/gpt-4o-mini"
    fi
    if [ "$(get_env FAST_MODEL)" = "not set" ]; then
        set_env "FAST_MODEL" "openai/gpt-4o-mini"
    fi
    if [ "$(get_env SMART_MODEL)" = "not set" ]; then
        set_env "SMART_MODEL" "anthropic/claude-3.5-sonnet"
    fi
    if [ "$(get_env GENIUS_MODEL)" = "not set" ]; then
        set_env "GENIUS_MODEL" "anthropic/claude-3-opus"
    fi
    if [ "$(get_env LLM_DAILY_BUDGET)" = "not set" ]; then
        set_env "LLM_DAILY_BUDGET" "100"
    fi

    echo -e "${GREEN}✅ Superhuman Streaming enabled!${NC}"
    echo ""
    show_status
}

# Function to disable features
disable_features() {
    echo -e "${YELLOW}⏸️  Disabling Superhuman Streaming Features...${NC}"

    set_env "ALLOW_MOCK_LLM" "false"
    set_env "ENABLE_HYBRID_STREAMING" "false"
    set_env "ENABLE_INTELLIGENT_ROUTING" "false"

    echo -e "${YELLOW}✅ Superhuman Streaming disabled (standard streaming active)${NC}"
    echo ""
    show_status
}

# Function to enable dev mode
enable_dev_mode() {
    echo -e "${BLUE}🔧 Enabling Development Mode...${NC}"

    set_env "ALLOW_MOCK_LLM" "true"
    set_env "ENABLE_HYBRID_STREAMING" "false"
    set_env "ENABLE_INTELLIGENT_ROUTING" "false"

    echo -e "${BLUE}✅ Development mode enabled (mock LLM active)${NC}"
    echo ""
    show_status
}

# Function to deploy nginx config
deploy_nginx() {
    echo -e "${BLUE}🌐 Deploying NGINX Configuration...${NC}"

    if [ ! -d "infra/nginx" ]; then
        echo -e "${RED}❌ Error: infra/nginx directory not found${NC}"
        exit 1
    fi

    echo ""
    echo -e "${YELLOW}📋 NGINX Configuration Files:${NC}"
    echo "  - infra/nginx/sse.conf         (SSE streaming config)"
    echo "  - infra/nginx/cogniforge-example.conf (Full example)"
    echo ""
    echo -e "${YELLOW}📝 Deployment Steps:${NC}"
    echo "  1. Copy configs to your NGINX server:"
    echo "     sudo cp infra/nginx/sse.conf /etc/nginx/snippets/"
    echo ""
    echo "  2. Include in your server block:"
    echo "     location /api/v1/stream/ {"
    echo "         include /etc/nginx/snippets/sse.conf;"
    echo "         proxy_pass http://backend;"
    echo "     }"
    echo ""
    echo "  3. Test and reload:"
    echo "     sudo nginx -t"
    echo "     sudo systemctl reload nginx"
    echo ""
    echo -e "${GREEN}✅ See infra/nginx/cogniforge-example.conf for complete example${NC}"
}

# Main script
case "$1" in
    enable)
        enable_features
        ;;
    disable)
        disable_features
        ;;
    dev)
        enable_dev_mode
        ;;
    status)
        show_status
        ;;
    nginx)
        deploy_nginx
        ;;
    *)
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}🚀 Superhuman Streaming Setup${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        echo "Usage: $0 {enable|disable|dev|status|nginx}"
        echo ""
        echo "Commands:"
        echo "  enable   - Enable all superhuman streaming features"
        echo "  disable  - Disable advanced features (standard streaming)"
        echo "  dev      - Enable development mode (mock LLM)"
        echo "  status   - Show current configuration status"
        echo "  nginx    - Show NGINX deployment instructions"
        echo ""
        echo "Examples:"
        echo "  $0 enable    # Enable for production"
        echo "  $0 dev       # Enable for development"
        echo "  $0 status    # Check current status"
        echo "  $0 nginx     # Deploy NGINX configs"
        echo ""
        exit 1
        ;;
esac
