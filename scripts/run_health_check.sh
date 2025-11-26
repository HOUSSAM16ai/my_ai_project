#!/usr/bin/env bash
# ==============================================================================
#
# Health Check Script (run_health_check.sh)
#
# هذا السكربت يتحقق من أن الخادم الخلفي (Backend) يعمل بشكل صحيح.
# يقوم بإرسال طلب إلى نقطة النهاية '/system/health' وينتظر استجابة ناجحة.
#
# تم إنشاؤه بناءً على تشخيص دقيق للمشكلة لضمان عدم تكرار الأخطاء السابقة.
#
# ==============================================================================

set -euo pipefail

# --- Configuration ---
BASE_URL="http://127.0.0.1:8000"
HEALTH_ENDPOINT="/system/health"
MAX_RETRIES=10
RETRY_DELAY_SECONDS=5
URL_TO_CHECK="${BASE_URL}${HEALTH_ENDPOINT}"

# --- ANSI Color Codes ---
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# --- Helper Functions ---
log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

# --- Main Logic ---
log_info "🚀 Starting Health Check..."
log_info "Target URL: ${URL_TO_CHECK}"
log_info "Max Retries: ${MAX_RETRIES}"
log_info "Delay between retries: ${RETRY_DELAY_SECONDS}s"
echo "------------------------------------------------------"

for i in $(seq 1 $MAX_RETRIES); do
    log_info "Attempt #${i} of ${MAX_RETRIES}..."

    # -s: silent mode
    # -f: fail silently on server errors (return non-zero exit code)
    # -o /dev/null: discard output
    if curl -s -f -o /dev/null "${URL_TO_CHECK}"; then
        echo "------------------------------------------------------"
        log_info "✅ SUCCESS: The server is healthy and responding correctly."
        log_info "🎉 كل شيء يعمل بنجاح 100%!"
        exit 0
    else
        log_warn "Server is not ready yet. Retrying in ${RETRY_DELAY_SECONDS} seconds..."
        sleep "${RETRY_DELAY_SECONDS}"
    fi
done

echo "------------------------------------------------------"
log_error "❌ FAILURE: The server did not become healthy after ${MAX_RETRIES} attempts."
log_error "Please check the server logs for more details."
exit 1
