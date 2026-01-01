#!/usr/bin/env bash
###############################################################################
# codespaces_diagnostic.sh - GitHub Codespaces Health Diagnostic
#
# تشخيص صحة بيئة GitHub Codespaces - أداة شاملة لفحص النظام
# Comprehensive health check tool for diagnosing application issues in Codespaces
# 
# Purpose:
#   Comprehensive health check for the application running in Codespaces
#   to diagnose crashes and performance issues
#
# Usage:
#   bash scripts/codespaces_diagnostic.sh
#
# Version: 1.0.0
# Date: 2026-01-01
###############################################################################

set -euo pipefail

readonly APP_PORT="${PORT:-8000}"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_ROOT="/app"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║       GitHub Codespaces Health Diagnostic v1.0.0                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    
    case "$status" in
        "OK")
            echo -e "${GREEN}✅ OK${NC} - $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC} - $message"
            ;;
        "ERROR")
            echo -e "${RED}❌ ERROR${NC} - $message"
            ;;
        *)
            echo "   $message"
            ;;
    esac
}

# ==============================================================================
# 1. ENVIRONMENT DETECTION
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. ENVIRONMENT DETECTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "${CODESPACES:-}" ]; then
    print_status "OK" "Running in GitHub Codespaces"
    echo "   Codespace Name: ${CODESPACE_NAME:-N/A}"
else
    print_status "WARN" "Not running in Codespaces - diagnostic may not be accurate"
fi

# ==============================================================================
# 2. SYSTEM RESOURCES
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. SYSTEM RESOURCES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# CPU
CPU_COUNT=$(nproc)
CPU_LOAD=$(uptime | awk -F'load average:' '{ print $2 }' | awk '{ print $1 }' | sed 's/,//')
print_status "OK" "CPUs: $CPU_COUNT cores, Load: $CPU_LOAD"

# Memory
TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
USED_MEM=$(free -h | awk '/^Mem:/ {print $3}')
MEM_PERCENT=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')

if [ "$MEM_PERCENT" -lt 80 ]; then
    print_status "OK" "Memory: $USED_MEM / $TOTAL_MEM used (${MEM_PERCENT}%)"
elif [ "$MEM_PERCENT" -lt 90 ]; then
    print_status "WARN" "Memory: $USED_MEM / $TOTAL_MEM used (${MEM_PERCENT}%) - High usage"
else
    print_status "ERROR" "Memory: $USED_MEM / $TOTAL_MEM used (${MEM_PERCENT}%) - CRITICAL"
fi

# Disk
DISK_USAGE=$(df -h "$APP_ROOT" 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//' || echo "0")
DISK_AVAIL=$(df -h "$APP_ROOT" 2>/dev/null | awk 'NR==2 {print $4}' || echo "N/A")

if [ -z "$DISK_USAGE" ] || [ "$DISK_USAGE" = "0" ]; then
    print_status "WARN" "Could not determine disk usage for $APP_ROOT"
elif [ "$DISK_USAGE" -lt 80 ]; then
    print_status "OK" "Disk: ${DISK_USAGE}% used, ${DISK_AVAIL} available"
elif [ "$DISK_USAGE" -lt 90 ]; then
    print_status "WARN" "Disk: ${DISK_USAGE}% used, ${DISK_AVAIL} available"
else
    print_status "ERROR" "Disk: ${DISK_USAGE}% used, ${DISK_AVAIL} available - LOW SPACE"
fi

# ==============================================================================
# 3. APPLICATION PROCESSES
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. APPLICATION PROCESSES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for Uvicorn
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    UVICORN_PID=$(pgrep -f "uvicorn.*app.main:app" | head -1)
    UVICORN_MEM=$(ps -p "$UVICORN_PID" -o %mem= | awk '{printf "%.1f", $1}')
    UVICORN_CPU=$(ps -p "$UVICORN_PID" -o %cpu= | awk '{printf "%.1f", $1}')
    print_status "OK" "Uvicorn running (PID: $UVICORN_PID, CPU: ${UVICORN_CPU}%, MEM: ${UVICORN_MEM}%)"
else
    print_status "ERROR" "Uvicorn is NOT running!"
fi

# Check for Supervisor
if pgrep -f "supervisor.sh" > /dev/null; then
    print_status "OK" "Supervisor is running"
else
    print_status "WARN" "Supervisor is NOT running"
fi

# ==============================================================================
# 4. NETWORK & PORTS
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. NETWORK & PORTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if port is listening
if netstat -tuln 2>/dev/null | grep -q ":${APP_PORT} "; then
    print_status "OK" "Port $APP_PORT is listening"
elif ss -tuln 2>/dev/null | grep -q ":${APP_PORT} "; then
    print_status "OK" "Port $APP_PORT is listening"
else
    print_status "ERROR" "Port $APP_PORT is NOT listening!"
fi

# ==============================================================================
# 5. APPLICATION HEALTH
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. APPLICATION HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Health endpoint check
HEALTH_URL="http://localhost:${APP_PORT}/health"
if HEALTH_RESPONSE=$(curl -sf "$HEALTH_URL" 2>&1); then
    if echo "$HEALTH_RESPONSE" | grep -q '"application":"ok"'; then
        print_status "OK" "Health endpoint is healthy"
        echo "   Response: $(echo "$HEALTH_RESPONSE" | head -c 100)..."
    else
        print_status "WARN" "Health endpoint responded but may not be healthy"
        echo "   Response: $HEALTH_RESPONSE"
    fi
else
    print_status "ERROR" "Health endpoint is not responding!"
    echo "   Error: $HEALTH_RESPONSE"
fi

# Root endpoint check
ROOT_URL="http://localhost:${APP_PORT}/"
if curl -sf -I "$ROOT_URL" > /dev/null 2>&1; then
    print_status "OK" "Root endpoint is accessible"
else
    print_status "ERROR" "Root endpoint is not accessible!"
fi

# ==============================================================================
# 6. CONFIGURATION FILES
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. CONFIGURATION FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$APP_ROOT" 2>/dev/null || cd /

# Check .env file
if [ -f ".env" ]; then
    ENV_SIZE=$(wc -c < .env)
    if [ "$ENV_SIZE" -gt 100 ]; then
        print_status "OK" ".env file exists (${ENV_SIZE} bytes)"
        
        # Check critical variables (without showing values)
        for var in DATABASE_URL SECRET_KEY; do
            if grep -q "^${var}=" .env; then
                print_status "OK" "  ✓ $var is set"
            else
                print_status "WARN" "  ✗ $var is NOT set"
            fi
        done
    else
        print_status "WARN" ".env file exists but seems too small (${ENV_SIZE} bytes)"
    fi
else
    print_status "ERROR" ".env file does NOT exist!"
fi

# Check static files
if [ -f "app/static/index.html" ]; then
    INDEX_SIZE=$(wc -c < app/static/index.html)
    print_status "OK" "index.html exists (${INDEX_SIZE} bytes)"
else
    print_status "ERROR" "index.html does NOT exist!"
fi

# ==============================================================================
# 7. RECENT LOGS
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. RECENT LOGS (Last 10 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for common log locations
for log_file in ".superhuman_bootstrap.log" ".devcontainer/supervisor.log" "app.log"; do
    if [ -f "$log_file" ]; then
        echo ""
        echo "📄 $log_file (last 10 lines):"
        tail -10 "$log_file" 2>/dev/null | sed 's/^/   /'
    fi
done

# Check journalctl if available
if command -v journalctl &> /dev/null; then
    echo ""
    echo "📄 System logs (last 5 entries):"
    journalctl -n 5 --no-pager 2>/dev/null | sed 's/^/   /' || echo "   (journalctl not accessible)"
fi

# ==============================================================================
# SUMMARY
# ==============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DIAGNOSTIC SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "If the application is crashing, check for:"
echo "  1. High memory usage (>90%) - indicates memory leak"
echo "  2. Uvicorn not running - process may have crashed"
echo "  3. Port not listening - server failed to start"
echo "  4. Health endpoint failing - application errors"
echo "  5. Missing .env or configuration - setup incomplete"
echo ""
echo "To view live logs: tail -f .superhuman_bootstrap.log"
echo "To restart: pkill -f uvicorn && bash .devcontainer/supervisor.sh"
echo ""
echo "╚══════════════════════════════════════════════════════════════════╝"
