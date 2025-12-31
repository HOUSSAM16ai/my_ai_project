#!/usr/bin/env bash
###############################################################################
# healthcheck.sh - Application Health Check Utility
#
# أداة فحص صحة التطبيق
# Application Health Check Utility
#
# الاستخدام (Usage):
#   bash .devcontainer/healthcheck.sh [--wait] [--timeout=30]
#
# الخيارات (Options):
#   --wait         Wait until application is healthy
#   --timeout=N    Timeout in seconds (default: 30)
#   --verbose      Show detailed output
#
# الإصدار (Version): 1.0.0
# التاريخ (Date): 2025-12-31
###############################################################################

set -Eeuo pipefail

# ==============================================================================
# CONFIGURATION (التكوين)
# ==============================================================================

readonly APP_PORT="${PORT:-8000}"
readonly HEALTH_URL="http://localhost:${APP_PORT}/health"
readonly DEFAULT_TIMEOUT=30

# Parse arguments
WAIT_MODE=false
TIMEOUT=$DEFAULT_TIMEOUT
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --wait)
            WAIT_MODE=true
            ;;
        --timeout=*)
            TIMEOUT="${arg#*=}"
            ;;
        --verbose)
            VERBOSE=true
            ;;
        --help)
            echo "Usage: $0 [--wait] [--timeout=N] [--verbose]"
            exit 0
            ;;
    esac
done

# ==============================================================================
# FUNCTIONS (الدوال)
# ==============================================================================

log() {
    if [ "$VERBOSE" = true ]; then
        echo "[$(date +'%H:%M:%S')] $1"
    fi
}

check_health() {
    local response
    local http_code
    
    # Check if port is listening
    if ! ss -tlnp 2>/dev/null | grep -q ":$APP_PORT "; then
        log "Port $APP_PORT is not listening"
        return 1
    fi
    
    # Check HTTP endpoint
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    
    if [ "$http_code" != "200" ]; then
        log "Health endpoint returned: $http_code"
        return 1
    fi
    
    # Verify response content
    response=$(curl -sf "$HEALTH_URL" 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q '"application":"ok"'; then
        return 0
    else
        log "Health response invalid: $response"
        return 1
    fi
}

# ==============================================================================
# MAIN LOGIC (المنطق الرئيسي)
# ==============================================================================

if [ "$WAIT_MODE" = true ]; then
    # Wait mode: retry until healthy or timeout
    log "Waiting for application health (timeout: ${TIMEOUT}s)..."
    
    elapsed=0
    while [ $elapsed -lt $TIMEOUT ]; do
        if check_health; then
            echo "✅ Application is healthy"
            exit 0
        fi
        
        sleep 1
        elapsed=$((elapsed + 1))
        
        if [ $((elapsed % 5)) -eq 0 ]; then
            log "Still waiting... (${elapsed}s elapsed)"
        fi
    done
    
    echo "❌ Timeout: Application did not become healthy within ${TIMEOUT}s"
    exit 1
else
    # Check mode: single check
    if check_health; then
        echo "✅ Application is healthy"
        exit 0
    else
        echo "❌ Application is not healthy"
        exit 1
    fi
fi
