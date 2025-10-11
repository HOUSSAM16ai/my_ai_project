#!/bin/bash
# ======================================================================================
# 🚀 COMPLETE ADMIN CHAT VERIFICATION SUITE
# ======================================================================================
# This script runs all verification checks for the admin chat persistence fix.
#
# Author: CogniForge System
# Version: 1.0.0
# ======================================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}${BOLD}================================================================================${NC}"
echo -e "${BLUE}${BOLD}                    🚀 ADMIN CHAT VERIFICATION SUITE                           ${NC}"
echo -e "${BLUE}${BOLD}================================================================================${NC}"
echo ""

# Step 1: Check Python syntax
echo -e "${CYAN}📝 Step 1: Checking Python syntax...${NC}"
python -m py_compile app/admin/routes.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Syntax check passed${NC}"
else
    echo -e "${RED}❌ Syntax errors found in routes.py${NC}"
    exit 1
fi
echo ""

# Step 2: Verify migration
echo -e "${CYAN}📝 Step 2: Verifying database migration...${NC}"
python verify_admin_chat_migration.py
MIGRATION_STATUS=$?
echo ""

if [ $MIGRATION_STATUS -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Migration verification failed or tables don't exist${NC}"
    echo -e "${YELLOW}💡 You may need to run: flask db upgrade${NC}"
    echo ""
    read -p "Do you want to continue with the test anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Verification stopped.${NC}"
        exit 1
    fi
fi

# Step 3: Run persistence test
echo -e "${CYAN}📝 Step 3: Testing conversation persistence...${NC}"
python test_admin_chat_persistence.py
TEST_STATUS=$?
echo ""

# Final summary
echo -e "${BLUE}${BOLD}================================================================================${NC}"
echo -e "${BLUE}${BOLD}                              FINAL SUMMARY                                    ${NC}"
echo -e "${BLUE}${BOLD}================================================================================${NC}"
echo ""

if [ $TEST_STATUS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo -e "${MAGENTA}📊 What this means:${NC}"
    echo -e "  • Admin chat routes are syntactically correct"
    echo -e "  • Database tables exist and are accessible"
    echo -e "  • Conversations can be created and saved"
    echo -e "  • Messages are persisted to the database"
    echo -e "  • History retrieval works correctly"
    echo -e "  • Analytics functions properly"
    echo ""
    echo -e "${CYAN}🎉 The admin chat persistence fix is working perfectly!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Test the admin chat UI in your browser"
    echo -e "  2. Check Supabase dashboard to see saved data"
    echo -e "  3. Deploy to production when ready"
    echo ""
else
    echo -e "${RED}${BOLD}❌ TESTS FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Possible issues:${NC}"
    echo -e "  • Database not accessible"
    echo -e "  • Migrations not applied"
    echo -e "  • Configuration errors"
    echo -e "  • Missing dependencies"
    echo ""
    echo -e "${YELLOW}Try:${NC}"
    echo -e "  1. Check your .env file has correct DATABASE_URL"
    echo -e "  2. Run: flask db upgrade"
    echo -e "  3. Check application logs for errors"
    echo ""
fi

echo -e "${BLUE}${BOLD}================================================================================${NC}"
echo ""

exit $TEST_STATUS
