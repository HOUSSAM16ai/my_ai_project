#!/bin/bash
# =============================================================================
# CogniForge Quick Fix Script
# سكريبت الإصلاح السريع
# =============================================================================
# This script performs quick fixes for common issues
# Better than tech giants because:
# - ✅ Automatic detection and fixing
# - ✅ User-friendly messages in Arabic & English
# - ✅ Safe with backups
# - ✅ Interactive mode
#
# Usage:
#   ./quick_fix.sh                 # Interactive mode
#   ./quick_fix.sh --auto          # Automatic mode
#   ./quick_fix.sh --check-only    # Check only, no fixes
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
AUTO_MODE=false
CHECK_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--auto] [--check-only]"
            echo "  --auto       : Run all fixes automatically without prompts"
            echo "  --check-only : Only check for issues, don't fix"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print header
print_header() {
    echo -e "${BOLD}${CYAN}================================================================================${NC}"
    echo -e "${BOLD}${CYAN}🔧 CogniForge Quick Fix - إصلاح سريع${NC}"
    echo -e "${BOLD}${CYAN}================================================================================${NC}"
    echo ""
    echo -e "${BLUE}📅 Timestamp:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}📂 Directory:${NC} $(pwd)"
    echo -e "${BLUE}🔧 Mode:${NC} $([ "$AUTO_MODE" = true ] && echo "Automatic" || echo "Interactive")"
    echo ""
}

# Function to print section
print_section() {
    echo ""
    echo -e "${BOLD}${MAGENTA}$1${NC}"
    echo -e "${BOLD}${MAGENTA}────────────────────────────────────────────────────────────────────────────────${NC}"
}

# Function to ask yes/no question
ask_yes_no() {
    if [ "$AUTO_MODE" = true ] || [ "$CHECK_ONLY" = true ]; then
        return 0  # Auto-yes in auto mode
    fi
    
    local question="$1"
    local default="${2:-n}"
    
    while true; do
        echo -ne "${YELLOW}$question [y/n] (default: $default): ${NC}"
        read -r response
        
        # Use default if empty
        response=${response:-$default}
        
        case "$response" in
            [Yy]* | [نن]* ) return 0 ;;
            [Nn]* ) return 1 ;;
            * ) echo -e "${RED}Please answer y or n${NC}" ;;
        esac
    done
}

# Function to check if file exists
check_file() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $description: Found${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: Not found${NC}"
        return 1
    fi
}

# Function to check .env file
check_env_file() {
    print_section "1️⃣ Checking .env file / فحص ملف .env"
    
    if check_file ".env" ".env file exists"; then
        # Check if it has real API keys
        if grep -q "OPENROUTER_API_KEY=sk-or-v1-xxx" .env 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Warning: .env contains example API key${NC}"
            echo -e "${YELLOW}   تحذير: ملف .env يحتوي على مفتاح مثال${NC}"
            return 1
        else
            echo -e "${GREEN}   ✓ .env appears to have real configuration${NC}"
            return 0
        fi
    else
        return 1
    fi
}

# Function to fix .env file
fix_env_file() {
    print_section "🔧 Fixing .env file / إصلاح ملف .env"
    
    if [ ! -f ".env.example" ]; then
        echo -e "${RED}❌ Cannot create .env: .env.example not found${NC}"
        return 1
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        echo -e "${YELLOW}   [CHECK-ONLY] Would create .env from .env.example${NC}"
        return 0
    fi
    
    # Backup existing .env if it exists
    if [ -f ".env" ]; then
        backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${BLUE}   📦 Backing up existing .env to $backup_file${NC}"
        cp .env "$backup_file"
    fi
    
    # Copy .env.example to .env
    echo -e "${BLUE}   📝 Creating .env from .env.example...${NC}"
    cp .env.example .env
    
    echo -e "${GREEN}   ✅ Created .env file${NC}"
    echo ""
    echo -e "${BOLD}${YELLOW}⚠️  IMPORTANT ACTION REQUIRED:${NC}"
    echo -e "${YELLOW}   You must add your API key to .env file:${NC}"
    echo ""
    echo -e "${CYAN}   1. Get your API key from: https://openrouter.ai/keys${NC}"
    echo -e "${CYAN}   2. Open .env file: nano .env${NC}"
    echo -e "${CYAN}   3. Find line: OPENROUTER_API_KEY=sk-or-v1-xxx...${NC}"
    echo -e "${CYAN}   4. Replace with your real key: OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY${NC}"
    echo -e "${CYAN}   5. Save and exit (Ctrl+O, Enter, Ctrl+X)${NC}"
    echo ""
    echo -e "${YELLOW}   عليك إضافة مفتاح API إلى ملف .env:${NC}"
    echo -e "${CYAN}   1. احصل على المفتاح من: https://openrouter.ai/keys${NC}"
    echo -e "${CYAN}   2. افتح .env: nano .env${NC}"
    echo -e "${CYAN}   3. استبدل المفتاح التجريبي بمفتاحك الحقيقي${NC}"
    echo -e "${CYAN}   4. احفظ واخرج${NC}"
    echo ""
    
    return 0
}

# Function to check API keys
check_api_keys() {
    print_section "2️⃣ Checking API Keys / فحص مفاتيح API"
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Cannot check: .env file not found${NC}"
        return 1
    fi
    
    # Check OPENROUTER_API_KEY
    local openrouter_key=$(grep "^OPENROUTER_API_KEY=" .env 2>/dev/null | cut -d'=' -f2)
    local openai_key=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d'=' -f2)
    
    local has_valid_key=false
    
    if [[ ! -z "$openrouter_key" && "$openrouter_key" != "sk-or-v1-xxx"* ]]; then
        echo -e "${GREEN}✅ OPENROUTER_API_KEY: Configured${NC}"
        has_valid_key=true
    else
        echo -e "${RED}❌ OPENROUTER_API_KEY: Not configured or using example key${NC}"
    fi
    
    if [[ ! -z "$openai_key" && "$openai_key" != "sk-xxx"* ]]; then
        echo -e "${GREEN}✅ OPENAI_API_KEY: Configured${NC}"
        has_valid_key=true
    else
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY: Not configured${NC}"
    fi
    
    if [ "$has_valid_key" = true ]; then
        echo -e "${GREEN}   ✓ At least one valid API key found${NC}"
        return 0
    else
        echo -e "${RED}   ✗ No valid API keys found${NC}"
        echo -e "${YELLOW}   📝 AI features will not work without API keys${NC}"
        return 1
    fi
}

# Function to check database connection
check_database() {
    print_section "3️⃣ Checking Database / فحص قاعدة البيانات"
    
    # Try to connect to database
    if python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.engine.connect(); print('OK')" 2>/dev/null | grep -q "OK"; then
        echo -e "${GREEN}✅ Database connection: OK${NC}"
        return 0
    else
        echo -e "${RED}❌ Database connection: Failed${NC}"
        echo -e "${YELLOW}   ⚠️  Check DATABASE_URL in .env${NC}"
        return 1
    fi
}

# Function to check and apply migrations
check_migrations() {
    print_section "4️⃣ Checking Migrations / فحص الهجرات"
    
    if ! command -v flask &> /dev/null; then
        echo -e "${YELLOW}⚠️  Flask command not found${NC}"
        return 1
    fi
    
    # Check current migration
    if flask db current &> /dev/null; then
        echo -e "${GREEN}✅ Database migrations: Applied${NC}"
        return 0
    else
        echo -e "${RED}❌ Database migrations: Not applied${NC}"
        return 1
    fi
}

# Function to apply migrations
fix_migrations() {
    print_section "🔧 Applying Migrations / تطبيق الهجرات"
    
    if [ "$CHECK_ONLY" = true ]; then
        echo -e "${YELLOW}   [CHECK-ONLY] Would apply database migrations${NC}"
        return 0
    fi
    
    echo -e "${BLUE}   🔄 Running flask db upgrade...${NC}"
    
    if flask db upgrade; then
        echo -e "${GREEN}   ✅ Migrations applied successfully${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Failed to apply migrations${NC}"
        return 1
    fi
}

# Function to check Python dependencies
check_dependencies() {
    print_section "5️⃣ Checking Dependencies / فحص التبعيات"
    
    local missing_deps=()
    local required_deps=("flask" "sqlalchemy" "openai" "requests" "python-dotenv")
    
    for dep in "${required_deps[@]}"; do
        if ! python3 -c "import ${dep//-/_}" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required dependencies: Installed${NC}"
        return 0
    else
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        return 1
    fi
}

# Function to install dependencies
fix_dependencies() {
    print_section "🔧 Installing Dependencies / تثبيت التبعيات"
    
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt not found${NC}"
        return 1
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        echo -e "${YELLOW}   [CHECK-ONLY] Would install dependencies from requirements.txt${NC}"
        return 0
    fi
    
    echo -e "${BLUE}   📦 Installing packages...${NC}"
    
    if pip3 install -r requirements.txt; then
        echo -e "${GREEN}   ✅ Dependencies installed${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Failed to install dependencies${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header
    
    # Track issues and fixes
    local issues_found=0
    local fixes_applied=0
    
    # 1. Check and fix .env
    if ! check_env_file; then
        ((issues_found++))
        if ask_yes_no "Create .env file from .env.example?" "y"; then
            if fix_env_file; then
                ((fixes_applied++))
            fi
        fi
    fi
    
    # 2. Check API keys
    if ! check_api_keys; then
        ((issues_found++))
        echo ""
        echo -e "${YELLOW}📌 Manual action required: Add API key to .env${NC}"
        echo -e "${YELLOW}   الإجراء المطلوب: أضف مفتاح API إلى .env${NC}"
    fi
    
    # 3. Check dependencies
    if ! check_dependencies; then
        ((issues_found++))
        if ask_yes_no "Install missing dependencies?" "y"; then
            if fix_dependencies; then
                ((fixes_applied++))
            fi
        fi
    fi
    
    # 4. Check database
    check_database
    db_ok=$?
    if [ $db_ok -ne 0 ]; then
        ((issues_found++))
    fi
    
    # 5. Check and fix migrations (only if database is OK)
    if [ $db_ok -eq 0 ]; then
        if ! check_migrations; then
            ((issues_found++))
            if ask_yes_no "Apply database migrations?" "y"; then
                if fix_migrations; then
                    ((fixes_applied++))
                fi
            fi
        fi
    fi
    
    # Print summary
    print_section "📊 Summary / الملخص"
    
    echo -e "${BOLD}Results:${NC}"
    echo -e "  Issues found: $issues_found"
    echo -e "  Fixes applied: $fixes_applied"
    echo ""
    
    if [ $issues_found -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✅ ALL CHECKS PASSED!${NC}"
        echo -e "${GREEN}System is configured correctly.${NC}"
        echo -e "${GREEN}النظام مُكون بشكل صحيح.${NC}"
        echo ""
        echo -e "${CYAN}🚀 You can now start the application:${NC}"
        echo -e "${CYAN}   flask run${NC}"
        echo -e "${CYAN}   # or${NC}"
        echo -e "${CYAN}   docker-compose up${NC}"
    else
        echo -e "${YELLOW}⚠️  Some issues need attention.${NC}"
        echo -e "${YELLOW}بعض المشاكل تحتاج إلى اهتمام.${NC}"
        echo ""
        
        if grep -q "OPENROUTER_API_KEY=sk-or-v1-xxx" .env 2>/dev/null; then
            echo -e "${BOLD}${RED}🚨 CRITICAL: API Key Not Configured${NC}"
            echo -e "${YELLOW}Please follow these steps:${NC}"
            echo -e "${CYAN}1. Get API key: https://openrouter.ai/keys${NC}"
            echo -e "${CYAN}2. Edit .env: nano .env${NC}"
            echo -e "${CYAN}3. Replace example key with your real key${NC}"
            echo -e "${CYAN}4. Save and restart application${NC}"
        fi
    fi
    
    echo ""
    echo -e "${BOLD}${CYAN}================================================================================${NC}"
    
    # Return exit code
    if [ $issues_found -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Run main function
main
exit $?
