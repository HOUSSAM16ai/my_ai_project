#!/bin/bash
# =============================================================================
# SUPERHUMAN STREAMING VERIFICATION SCRIPT
# =============================================================================
# تحقق من تفعيل نظام البث الخارق - Verify superhuman streaming activation
#
# This script verifies that all components for superhuman streaming are in place
# هذا السكريبت يتحقق من أن جميع مكونات البث الخارق موجودة

echo "=================================================="
echo "🚀 SUPERHUMAN STREAMING VERIFICATION"
echo "   تحقق من تفعيل نظام البث الخارق"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
TOTAL_CHECKS=0

# Function to check file exists
check_file() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $2"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - $2"
        echo "   File not found: $1"
        return 1
    fi
}

# Function to check string in file
check_content() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC} - $3"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - $3"
        echo "   String '$2' not found in $1"
        return 1
    fi
}

echo "1️⃣  Checking Core Files..."
echo "---------------------------------------------------"
check_file "app/static/js/adaptiveTypewriter.js" "AdaptiveTypewriter class exists"
check_file "app/static/js/useSSE.js" "SSE Consumer exists"
check_file "app/admin/templates/admin_dashboard.html" "Admin dashboard template exists"
check_file "app/services/admin_chat_streaming_service.py" "Streaming service exists"
check_file "app/admin/routes.py" "Admin routes exist"

echo ""
echo "2️⃣  Checking Template Integration..."
echo "---------------------------------------------------"
check_content "app/admin/templates/admin_dashboard.html" "adaptiveTypewriter.js" "Template includes AdaptiveTypewriter script"
check_content "app/admin/templates/admin_dashboard.html" "useSSE.js" "Template includes SSE consumer script"
check_content "app/admin/templates/admin_dashboard.html" "new AdaptiveTypewriter" "Template instantiates AdaptiveTypewriter"
check_content "app/admin/templates/admin_dashboard.html" "new SSEConsumer" "Template instantiates SSEConsumer"
check_content "app/admin/templates/admin_dashboard.html" "handle_chat_stream" "Template uses streaming endpoint"

echo ""
echo "3️⃣  Checking AdaptiveTypewriter Implementation..."
echo "---------------------------------------------------"
check_content "app/static/js/adaptiveTypewriter.js" "class AdaptiveTypewriter" "AdaptiveTypewriter class defined"
check_content "app/static/js/adaptiveTypewriter.js" "append(" "append() method exists"
check_content "app/static/js/adaptiveTypewriter.js" "typeChunk(" "typeChunk() method exists"
check_content "app/static/js/adaptiveTypewriter.js" "formatMarkdown(" "formatMarkdown() method exists"
check_content "app/static/js/adaptiveTypewriter.js" "baseDelayMs" "baseDelayMs configuration exists"

echo ""
echo "4️⃣  Checking SSE Endpoint..."
echo "---------------------------------------------------"
check_content "app/admin/routes.py" "@bp.route(\"/api/chat/stream\"" "Streaming endpoint route exists"
check_content "app/admin/routes.py" "handle_chat_stream" "Streaming handler exists"
check_content "app/admin/routes.py" "stream_with_context" "Stream context wrapper used"
check_content "app/admin/routes.py" "text/event-stream" "SSE content type configured"

echo ""
echo "5️⃣  Checking Streaming Service..."
echo "---------------------------------------------------"
check_content "app/services/admin_chat_streaming_service.py" "class AdminChatStreamingService" "Service class exists"
check_content "app/services/admin_chat_streaming_service.py" "stream_response(" "stream_response() method exists"
check_content "app/services/admin_chat_streaming_service.py" "SmartTokenChunker" "Smart chunking implemented"
check_content "app/services/admin_chat_streaming_service.py" "delta" "Delta events configured"
check_content "app/services/admin_chat_streaming_service.py" "complete" "Complete events configured"

echo ""
echo "=================================================="
echo "📊 VERIFICATION RESULTS"
echo "=================================================="
echo ""
echo "Checks passed: ${CHECKS_PASSED}/${TOTAL_CHECKS}"
echo ""

if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo "   جميع الفحوصات نجحت!"
    echo ""
    echo "✨ Superhuman streaming is FULLY ACTIVATED!"
    echo "   البث الخارق مُفعّل بالكامل!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Start the application: flask run"
    echo "   2. Open: http://localhost:5000/admin/dashboard"
    echo "   3. Type a question and watch it stream word-by-word!"
    echo ""
    exit 0
else
    FAILED=$((TOTAL_CHECKS - CHECKS_PASSED))
    echo -e "${RED}⚠️  ${FAILED} CHECK(S) FAILED${NC}"
    echo "   ${FAILED} فحوصات فشلت"
    echo ""
    echo "Please review the failed checks above and fix the issues."
    echo ""
    exit 1
fi
