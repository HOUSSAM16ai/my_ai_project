#!/usr/bin/env bash
###############################################################################
# diagnostics.sh - System Diagnostics and Troubleshooting Tool
#
# أداة تشخيص النظام واستكشاف الأخطاء
# System Diagnostics and Troubleshooting Tool
#
# الاستخدام (Usage):
#   bash .devcontainer/diagnostics.sh [--full] [--export]
#
# الخيارات (Options):
#   --full     Run comprehensive diagnostics
#   --export   Export report to file
#   --help     Show this help message
#
# الإصدار (Version): 1.0.0
# التاريخ (Date): 2025-12-31
###############################################################################

set -Eeuo pipefail

# ==============================================================================
# CONFIGURATION (التكوين)
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_ROOT="/app"
readonly REPORT_FILE="$APP_ROOT/.diagnostics_report_$(date +%Y%m%d_%H%M%S).txt"

# Parse arguments
FULL_MODE=false
EXPORT_MODE=false

for arg in "$@"; do
    case $arg in
        --full)
            FULL_MODE=true
            ;;
        --export)
            EXPORT_MODE=true
            ;;
        --help)
            head -n 20 "$0" | tail -n +2 | sed 's/^# //'
            exit 0
            ;;
    esac
done

# Load core library if available
if [ -f "$SCRIPT_DIR/lib/lifecycle_core.sh" ]; then
    source "$SCRIPT_DIR/lib/lifecycle_core.sh"
fi

# ==============================================================================
# DIAGNOSTIC FUNCTIONS (دوال التشخيص)
# ==============================================================================

print_section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
}

check_system_info() {
    print_section "System Information | معلومات النظام"
    
    echo "Hostname: $(hostname)"
    echo "Kernel: $(uname -r)"
    echo "OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo 'Unknown')"
    echo "Uptime: $(uptime -p 2>/dev/null || echo 'N/A')"
    echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
}

check_resources() {
    print_section "Resource Usage | استخدام الموارد"
    
    echo "=== CPU ==="
    top -bn1 | head -5
    
    echo ""
    echo "=== Memory ==="
    free -h
    
    echo ""
    echo "=== Disk ==="
    df -h /app 2>/dev/null || df -h /
    
    if [ "$FULL_MODE" = true ]; then
        echo ""
        echo "=== Top Processes ==="
        ps aux --sort=-%mem | head -10
    fi
}

check_network() {
    print_section "Network Status | حالة الشبكة"
    
    echo "=== Listening Ports ==="
    ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || echo "No network tools available"
    
    echo ""
    echo "=== DNS Resolution ==="
    if command -v nslookup >/dev/null 2>&1; then
        nslookup google.com 2>&1 | head -5
    else
        echo "nslookup not available"
    fi
}

check_application() {
    print_section "Application Status | حالة التطبيق"
    
    local app_port="${PORT:-8000}"
    local health_url="http://localhost:${app_port}/health"
    
    echo "=== Process Status ==="
    if pgrep -f "uvicorn" >/dev/null 2>&1; then
        echo "✅ Uvicorn is running"
        ps aux | grep -E "uvicorn|python" | grep -v grep
    else
        echo "❌ Uvicorn is NOT running"
    fi
    
    echo ""
    echo "=== Port Status ==="
    if ss -tlnp 2>/dev/null | grep -q ":$app_port "; then
        echo "✅ Port $app_port is listening"
    else
        echo "❌ Port $app_port is NOT listening"
    fi
    
    echo ""
    echo "=== Health Check ==="
    if command -v curl >/dev/null 2>&1; then
        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")
        
        if [ "$http_code" = "200" ]; then
            echo "✅ Health endpoint is responding (HTTP $http_code)"
            curl -sf "$health_url" 2>/dev/null | head -5
        else
            echo "❌ Health endpoint is NOT responding (HTTP $http_code)"
        fi
    else
        echo "curl not available"
    fi
}

check_environment() {
    print_section "Environment Configuration | تكوين البيئة"
    
    echo "=== Environment Variables ==="
    env | grep -E "^(DATABASE_URL|SECRET_KEY|ADMIN_|ENVIRONMENT|TESTING|PORT)" | sed 's/=.*/=***/' || echo "No relevant env vars found"
    
    echo ""
    echo "=== .env File ==="
    if [ -f "$APP_ROOT/.env" ]; then
        echo "✅ .env file exists"
        echo "Size: $(wc -c < "$APP_ROOT/.env") bytes"
        echo "Lines: $(wc -l < "$APP_ROOT/.env")"
    else
        echo "❌ .env file NOT found"
    fi
    
    echo ""
    echo "=== Python Environment ==="
    python --version 2>/dev/null || echo "Python not found"
    echo "Packages installed: $(pip list 2>/dev/null | wc -l)"
}

check_logs() {
    print_section "Recent Logs | السجلات الأخيرة"
    
    local log_file="$APP_ROOT/.superhuman_bootstrap.log"
    
    if [ -f "$log_file" ]; then
        echo "=== Last 20 lines of bootstrap log ==="
        tail -20 "$log_file"
        
        echo ""
        echo "=== Errors in log ==="
        grep -i "error\|fail\|critical" "$log_file" 2>/dev/null | tail -10 || echo "No errors found"
    else
        echo "❌ Bootstrap log not found: $log_file"
    fi
}

check_lifecycle_state() {
    print_section "Lifecycle State | حالة دورة الحياة"
    
    local state_dir="$APP_ROOT/.devcontainer/state"
    
    if [ -d "$state_dir" ]; then
        echo "=== State Files ==="
        ls -lh "$state_dir" 2>/dev/null || echo "No state files"
        
        echo ""
        echo "=== State Values ==="
        for state_file in "$state_dir"/*; do
            if [ -f "$state_file" ]; then
                local state_name=$(basename "$state_file")
                local state_value=$(cat "$state_file")
                echo "  $state_name: $state_value"
            fi
        done
    else
        echo "❌ State directory not found: $state_dir"
    fi
}

check_docker() {
    if [ "$FULL_MODE" = true ]; then
        print_section "Docker Information | معلومات Docker"
        
        if command -v docker >/dev/null 2>&1; then
            echo "=== Docker Version ==="
            docker --version
            
            echo ""
            echo "=== Container Info ==="
            docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}" 2>/dev/null || echo "Cannot access Docker"
        else
            echo "Docker command not available"
        fi
    fi
}

generate_recommendations() {
    print_section "Recommendations | التوصيات"
    
    local issues=()
    
    # Check if app is running
    if ! pgrep -f "uvicorn" >/dev/null 2>&1; then
        issues+=("Application is not running. Try: bash .devcontainer/supervisor.sh")
    fi
    
    # Check if port is listening
    if ! ss -tlnp 2>/dev/null | grep -q ":${PORT:-8000} "; then
        issues+=("Port ${PORT:-8000} is not listening. Check if Uvicorn started successfully.")
    fi
    
    # Check memory usage
    local mem_percent
    mem_percent=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')
    if [ "$mem_percent" -gt 80 ]; then
        issues+=("High memory usage (${mem_percent}%). Consider restarting the container.")
    fi
    
    # Display issues
    if [ ${#issues[@]} -gt 0 ]; then
        echo "⚠️  Issues Found:"
        for issue in "${issues[@]}"; do
            echo "  • $issue"
        done
    else
        echo "✅ No issues detected"
    fi
    
    echo ""
    echo "📚 Useful Commands:"
    echo "  • View logs:        tail -f .superhuman_bootstrap.log"
    echo "  • Check health:     bash .devcontainer/healthcheck.sh"
    echo "  • Restart app:      pkill -f uvicorn && bash .devcontainer/supervisor.sh"
    echo "  • Full diagnostics: bash .devcontainer/diagnostics.sh --full"
}

# ==============================================================================
# MAIN EXECUTION (التنفيذ الرئيسي)
# ==============================================================================

main() {
    local output=""
    
    # Redirect output if export mode
    if [ "$EXPORT_MODE" = true ]; then
        exec > >(tee "$REPORT_FILE")
    fi
    
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  CogniForge System Diagnostics"
    echo "  تشخيص نظام CogniForge"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "  Mode: $([ "$FULL_MODE" = true ] && echo "Full" || echo "Quick")"
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Run diagnostics
    check_system_info
    check_resources
    check_network
    check_application
    check_environment
    check_logs
    check_lifecycle_state
    check_docker
    generate_recommendations
    
    # Final message
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Diagnostics Complete"
    echo "═══════════════════════════════════════════════════════════════════"
    
    if [ "$EXPORT_MODE" = true ]; then
        echo ""
        echo "📄 Report exported to: $REPORT_FILE"
    fi
}

# Run main function
main
