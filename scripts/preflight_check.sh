#!/bin/bash

# Pre-flight check script for Step 1

# Exit on error
set -e

# --- Configuration ---
REPORTS_DIR="reports"
LOG_FILE="$REPORTS_DIR/preflight.log"
JSON_REPORT_FILE="$REPORTS_DIR/step1_preflight.json"

# --- Setup ---
mkdir -p "$REPORTS_DIR"
touch "$LOG_FILE"
touch "$JSON_REPORT_FILE"

# --- Functions ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- Main ---
log "Starting pre-flight checks..."

# 1. Import checks
log "Running import checks..."
FLASK_IMPORTS=$(grep -r "from flask import" app | wc -l)
CURRENT_APP_USAGES=$(grep -r "current_app" app | wc -l)
APP_CONTEXT_USAGES=$(grep -r "app_context" app | wc -l)
FLASK_LOGIN_IMPORTS=$(grep -r "flask_login" app | wc -l)
BLUEPRINT_USAGES=$(grep -r "Blueprint" app | wc -l)

# 2. Minimal get_db() test
log "Running minimal get_db() test..."
python3 -c "from app.core.deps import get_db; next(get_db())" >> "$LOG_FILE" 2>&1

# 3. Validate settings
log "Validating settings..."
python3 -c "from app.core.config import get_settings; get_settings()" >> "$LOG_FILE" 2>&1

# 4. Lint quick-pass
log "Running lint quick-pass..."
ruff check . >> "$LOG_FILE" 2>&1 || true

# 5. Write reports
log "Writing reports..."
cat <<EOF > "$JSON_REPORT_FILE"
{
  "flask_imports": $FLASK_IMPORTS,
  "current_app_usages": $CURRENT_APP_USAGES,
  "app_context_usages": $APP_CONTEXT_USAGES,
  "flask_login_imports": $FLASK_LOGIN_IMPORTS,
  "blueprint_usages": $BLUEPRINT_USAGES
}
EOF

log "Pre-flight checks complete."
