#!/bin/bash
# ======================================================================================
# ULTIMATE MODE QUICK ENABLER - مُفَعِّل الوضع الخارق السريع
# ======================================================================================
# This script helps you quickly enable ULTIMATE or EXTREME mode for complex questions
# يساعدك هذا السكريبت على تفعيل الوضع الخارق أو الشديد بسرعة للأسئلة المعقدة

set -e

# Resolve project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
ROCKET="🚀"
FIRE="💪"
CHECK="✅"
WARN="⚠️"
INFO="ℹ️"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}     ${ROCKET} ULTIMATE MODE ENABLER ${ROCKET}${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${WARN} ${YELLOW}.env file not found. Creating from .env.example...${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${CHECK} ${GREEN}.env file created!${NC}"
    else
        echo -e "${RED}Error: .env.example not found!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${INFO} ${CYAN}Select the mode you want to enable:${NC}"
echo ""
echo -e "  ${GREEN}1)${NC} ${FIRE} EXTREME MODE ${FIRE}"
echo -e "     - Timeout: 10 minutes"
echo -e "     - Retries: 8 attempts"
echo -e "     - Max tokens: 64,000"
echo -e "     - Best for: Very complex questions"
echo ""
echo -e "  ${GREEN}2)${NC} ${ROCKET} ULTIMATE MODE ${ROCKET} ${YELLOW}(SUPERHUMAN!)${NC}"
echo -e "     - Timeout: 30 minutes"
echo -e "     - Retries: 20 attempts"
echo -e "     - Max tokens: 128,000"
echo -e "     - Best for: Mission-critical questions"
echo ""
echo -e "  ${GREEN}3)${NC} Disable both (return to Normal mode)"
echo ""
echo -e "  ${GREEN}4)${NC} Show current configuration"
echo ""
echo -e "  ${GREEN}5)${NC} Exit"
echo ""

read -p "$(echo -e ${CYAN}Enter your choice [1-5]:${NC} )" choice

case $choice in
    1)
        echo ""
        echo -e "${FIRE} ${YELLOW}Enabling EXTREME MODE...${NC}"
        
        # Remove ULTIMATE mode if exists
        sed -i '/^LLM_ULTIMATE_COMPLEXITY_MODE=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
        
        # Add or update EXTREME mode
        if grep -q "^LLM_EXTREME_COMPLEXITY_MODE=" "$PROJECT_ROOT/.env"; then
            sed -i 's/^LLM_EXTREME_COMPLEXITY_MODE=.*/LLM_EXTREME_COMPLEXITY_MODE=1/' "$PROJECT_ROOT/.env"
        else
            echo "" >> "$PROJECT_ROOT/.env"
            echo "# EXTREME MODE - Enabled by quick-enable script" >> "$PROJECT_ROOT/.env"
            echo "LLM_EXTREME_COMPLEXITY_MODE=1" >> "$PROJECT_ROOT/.env"
        fi
        
        echo -e "${CHECK} ${GREEN}EXTREME MODE enabled!${NC}"
        echo ""
        echo -e "${INFO} Configuration:"
        echo -e "  - Timeout: ${YELLOW}600 seconds (10 minutes)${NC}"
        echo -e "  - Retries: ${YELLOW}8 attempts${NC}"
        echo -e "  - Max tokens: ${YELLOW}64,000${NC}"
        ;;
        
    2)
        echo ""
        echo -e "${ROCKET} ${YELLOW}Enabling ULTIMATE MODE...${NC}"
        
        # Remove EXTREME mode if exists
        sed -i '/^LLM_EXTREME_COMPLEXITY_MODE=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
        
        # Add or update ULTIMATE mode
        if grep -q "^LLM_ULTIMATE_COMPLEXITY_MODE=" "$PROJECT_ROOT/.env"; then
            sed -i 's/^LLM_ULTIMATE_COMPLEXITY_MODE=.*/LLM_ULTIMATE_COMPLEXITY_MODE=1/' "$PROJECT_ROOT/.env"
        else
            echo "" >> "$PROJECT_ROOT/.env"
            echo "# ULTIMATE MODE - Enabled by quick-enable script" >> "$PROJECT_ROOT/.env"
            echo "LLM_ULTIMATE_COMPLEXITY_MODE=1" >> "$PROJECT_ROOT/.env"
        fi
        
        echo -e "${CHECK} ${GREEN}ULTIMATE MODE enabled!${NC}"
        echo ""
        echo -e "${INFO} Configuration:"
        echo -e "  - Timeout: ${YELLOW}1800 seconds (30 minutes!)${NC}"
        echo -e "  - Retries: ${YELLOW}20 attempts${NC}"
        echo -e "  - Max tokens: ${YELLOW}128,000${NC}"
        echo ""
        echo -e "${ROCKET} ${MAGENTA}SUPERHUMAN MODE ACTIVATED!${NC}"
        ;;
        
    3)
        echo ""
        echo -e "${INFO} ${YELLOW}Disabling special modes...${NC}"
        
        # Remove both modes
        sed -i '/^LLM_EXTREME_COMPLEXITY_MODE=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
        sed -i '/^LLM_ULTIMATE_COMPLEXITY_MODE=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
        
        echo -e "${CHECK} ${GREEN}Returned to Normal mode${NC}"
        echo ""
        echo -e "${INFO} Configuration:"
        echo -e "  - Timeout: ${YELLOW}180 seconds (3 minutes)${NC}"
        echo -e "  - Retries: ${YELLOW}2 attempts${NC}"
        echo -e "  - Max tokens: ${YELLOW}4,000${NC}"
        ;;
        
    4)
        echo ""
        echo -e "${INFO} ${CYAN}Current Configuration:${NC}"
        echo ""
        
        if grep -q "^LLM_ULTIMATE_COMPLEXITY_MODE=1" "$PROJECT_ROOT/.env" 2>/dev/null; then
            echo -e "  Mode: ${ROCKET} ${MAGENTA}ULTIMATE MODE${NC} ${CHECK}"
            echo -e "  - Timeout: ${YELLOW}1800 seconds (30 minutes)${NC}"
            echo -e "  - Retries: ${YELLOW}20 attempts${NC}"
            echo -e "  - Max tokens: ${YELLOW}128,000${NC}"
        elif grep -q "^LLM_EXTREME_COMPLEXITY_MODE=1" "$PROJECT_ROOT/.env" 2>/dev/null; then
            echo -e "  Mode: ${FIRE} ${YELLOW}EXTREME MODE${NC} ${CHECK}"
            echo -e "  - Timeout: ${YELLOW}600 seconds (10 minutes)${NC}"
            echo -e "  - Retries: ${YELLOW}8 attempts${NC}"
            echo -e "  - Max tokens: ${YELLOW}64,000${NC}"
        else
            echo -e "  Mode: ${GREEN}Normal Mode${NC}"
            echo -e "  - Timeout: ${YELLOW}180 seconds (3 minutes)${NC}"
            echo -e "  - Retries: ${YELLOW}2 attempts${NC}"
            echo -e "  - Max tokens: ${YELLOW}4,000${NC}"
        fi
        
        echo ""
        exit 0
        ;;
        
    5)
        echo ""
        echo -e "${INFO} ${CYAN}Exiting...${NC}"
        exit 0
        ;;
        
    *)
        echo ""
        echo -e "${RED}Invalid choice. Exiting...${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${INFO} ${YELLOW}Next Steps:${NC}"
echo ""
echo -e "  1. Restart your application for changes to take effect:"
echo -e "     ${BLUE}docker-compose down && docker-compose up -d${NC}"
echo ""
echo -e "  2. Or if running locally:"
echo -e "     ${BLUE}python -m uvicorn app.main:app --reload${NC}"
echo ""
echo -e "  3. Test with a complex question:"
echo -e "     ${BLUE}curl -X POST http://localhost:8000/api/v1/chat/completions -H \"Content-Type: application/json\" -d '{\"prompt\": \"Your complex question here...\"}'${NC}"
echo ""
echo -e "${INFO} For more information, see ${GREEN}ULTIMATE_MODE_GUIDE.md${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Offer to restart if docker-compose is running
if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        echo ""
        read -p "$(echo -e ${YELLOW}Docker containers detected. Restart now? [y/N]:${NC} )" restart
        if [[ "$restart" =~ ^[Yy]$ ]]; then
            echo ""
            echo -e "${INFO} ${YELLOW}Restarting containers...${NC}"
            docker-compose down
            docker-compose up -d
            echo -e "${CHECK} ${GREEN}Containers restarted!${NC}"
            echo ""
            echo -e "${INFO} Check logs with: ${BLUE}docker-compose logs -f web${NC}"
        fi
    fi
fi

echo ""
echo -e "${CHECK} ${GREEN}Done! Your mode has been configured.${NC}"
echo ""
