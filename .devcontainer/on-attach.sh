#!/usr/bin/env bash
###############################################################################
# on-attach.sh - DevContainer Post-Attach Hook (v2.0)
#
# يُنفَّذ عند إرفاق IDE بالحاوية
# Executed when IDE attaches to the container
#
# المسؤوليات (Responsibilities):
#   1. عرض حالة النظام
#   2. إظهار معلومات الوصول
#   3. تقديم أوامر مفيدة
#
# المبادئ (Principles):
#   - Informational Only: No execution, just display
#   - Fast: < 1 second
#   - User-Friendly: Clear, actionable information
#
# الإصدار (Version): 2.0.0
# التاريخ (Date): 2025-12-31
###############################################################################

set -Eeuo pipefail

# ==============================================================================
# INITIALIZATION (التهيئة)
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_ROOT="/app"
readonly LOG_FILE="$APP_ROOT/.superhuman_bootstrap.log"
readonly APP_PORT="${PORT:-8000}"

cd "$APP_ROOT"

# Load core library
if [ -f "$SCRIPT_DIR/lib/lifecycle_core.sh" ]; then
    source "$SCRIPT_DIR/lib/lifecycle_core.sh"
else
    echo "⚠️  Warning: lifecycle_core.sh not found"
fi

# ==============================================================================
# STATUS DISPLAY (عرض الحالة)
# ==============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "🎯 CogniForge Development Environment"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Check application status
if lifecycle_check_http "http://localhost:$APP_PORT/health" 200 2>/dev/null; then
    echo "✅ Application Status: ${COLOR_GREEN}HEALTHY${COLOR_RESET}"
    echo "   🌐 Access: http://localhost:$APP_PORT"
    echo ""
else
    echo "⏳ Application Status: ${COLOR_YELLOW}STARTING${COLOR_RESET}"
    echo "   📝 Monitor: tail -f $LOG_FILE"
    echo "   ⏱️  Expected: 30-45 seconds from container start"
    echo ""
fi

# System information
echo "📊 System Information:"
echo "   • Python: $(python --version 2>/dev/null | cut -d' ' -f2 || echo 'N/A')"
echo "   • Working Directory: $(pwd)"
echo "   • Container: $(hostname)"
echo ""

# Useful commands
echo "🔧 Useful Commands:"
echo "   • View logs:        tail -f $LOG_FILE"
echo "   • Check health:     curl http://localhost:$APP_PORT/health"
echo "   • Restart app:      pkill -f uvicorn && bash .devcontainer/supervisor.sh"
echo "   • Run tests:        pytest tests/"
echo "   • Check processes:  ps aux | grep python"
echo ""

# State information (if available)
if command -v lifecycle_has_state >/dev/null 2>&1; then
    if lifecycle_has_state "app_ready"; then
        echo "🎉 All systems operational!"
    else
        echo "⏳ System is initializing..."
        echo "   Check $LOG_FILE for progress"
    fi
    echo ""
fi

echo "═══════════════════════════════════════════════════════════════════"
echo "💡 Tip: Wait for 'Application is healthy' message before accessing"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

exit 0
