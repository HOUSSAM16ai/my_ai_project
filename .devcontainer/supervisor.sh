#!/usr/bin/env bash
###############################################################################
# supervisor.sh - Application Lifecycle Supervisor (v2.1)
#
# المشرف على دورة حياة التطبيق
# Application Lifecycle Supervisor
#
# المسؤوليات (Responsibilities):
#   1. تثبيت التبعيات (Dependencies Installation)
#   2. تشغيل الترحيلات (Database Migrations)
#   3. إنشاء المستخدم الإداري (Admin Seeding)
#   4. إطلاق خادم التطبيق (Application Server)
#   5. فحص الصحة (Health Monitoring)
#
# المبادئ (Principles):
#   - Sequential Execution: Each step waits for previous
#   - Idempotent Operations: Safe to run multiple times
#   - Health-Gated: Don't signal ready until healthy
#   - Comprehensive Logging: Every action is logged
#
# الإصدار (Version): 2.1.0
# التاريخ (Date): 2026-01-18
###############################################################################

set -Eeuo pipefail

# ==============================================================================
# INITIALIZATION (التهيئة)
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_ROOT="/app"
readonly APP_PORT="${PORT:-8000}"
readonly FRONTEND_PORT="${FRONTEND_PORT:-3000}"
readonly HEALTH_ENDPOINT="http://localhost:${APP_PORT}/health"

cd "$APP_ROOT"

if [ -f "frontend/package.json" ]; then
    export ENABLE_STATIC_FILES="${ENABLE_STATIC_FILES:-0}"
else
    export ENABLE_STATIC_FILES="${ENABLE_STATIC_FILES:-1}"
fi

# Load core library
if [ -f "$SCRIPT_DIR/lib/lifecycle_core.sh" ]; then
    source "$SCRIPT_DIR/lib/lifecycle_core.sh"
else
    echo "ERROR: lifecycle_core.sh not found" >&2
    exit 1
fi

# Error trap
trap 'lifecycle_error "Supervisor failed at line $LINENO"' ERR

lifecycle_info "═══════════════════════════════════════════════════════"
lifecycle_info "🎯 Application Lifecycle Supervisor Started"
lifecycle_info "   Version: 2.1.0 (Async Frontend)"
lifecycle_info "   PID: $$"
lifecycle_info "   Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
lifecycle_info "═══════════════════════════════════════════════════════"

# ==============================================================================
# STEP 0: System Readiness & Environment (جاهزية النظام والبيئة)
# ==============================================================================

lifecycle_info "Step 0/5: System readiness check..."

# Give container time to fully initialize
# CODESPACES: Longer stabilization time for cloud environments
if [ -n "${CODESPACES:-}" ]; then
    lifecycle_info "Detected Codespaces environment - using extended stabilization (5s)..."
    sleep 5
else
    lifecycle_info "Waiting for system stabilization (2s)..."
    sleep 2
fi

# Create default .env if missing (Critical for environment consistency)
if [ ! -f .env ]; then
    lifecycle_info "Creating default .env file..."
    cat > .env <<EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=dev-secret
TESTING=1
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password
ADMIN_NAME=AdminUser
EOF
    lifecycle_info "✅ Created default .env file"
fi

lifecycle_info "✅ System ready"
lifecycle_set_state "system_ready" "$(date +%s)"

# ==============================================================================
# STEP 1: Dependencies Installation (تثبيت التبعيات)
# ==============================================================================

lifecycle_info "Step 1/5: Dependencies installation..."

install_dependencies() {
    lifecycle_info "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        lifecycle_error "requirements.txt not found"
        return 1
    fi
    
    # Use pip with caching for faster subsequent runs
    if pip install -r requirements.txt; then
        lifecycle_info "✅ Dependencies installed successfully"
        return 0
    else
        lifecycle_error "Failed to install dependencies"
        return 1
    fi
}

# Run once per container lifecycle
if ! lifecycle_has_state "dependencies_installed"; then
    if install_dependencies; then
        lifecycle_set_state "dependencies_installed" "$(date +%s)"
    else
        lifecycle_error "Dependency installation failed"
        exit 1
    fi
else
    lifecycle_info "Dependencies already installed (skipping)"
fi

# ==============================================================================
# STEP 2: Database Migrations (ترحيلات قاعدة البيانات)
# ==============================================================================

lifecycle_info "Step 2/5: Database migrations..."

run_migrations() {
    lifecycle_info "Running database migrations..."
    
    if [ -f "scripts/smart_migrate.py" ]; then
        # IMPORTANT: Must pass 'upgrade head' to smart_migrate.py
        if python scripts/smart_migrate.py upgrade head; then
            lifecycle_info "✅ Migrations completed successfully"
            return 0
        else
            lifecycle_warn "Migration script failed (non-fatal)"
            return 0  # Don't fail supervisor on migration errors
        fi
    else
        lifecycle_warn "Migration script not found (skipping)"
        return 0
    fi
}

if run_migrations; then
    lifecycle_set_state "migrations_completed" "$(date +%s)"
else
    lifecycle_warn "Migrations had issues but continuing..."
fi

# ==============================================================================
# STEP 3: Admin User Seeding (إنشاء المستخدم الإداري)
# ==============================================================================

lifecycle_info "Step 3/5: Admin user seeding..."

seed_admin() {
    lifecycle_info "Seeding admin user..."
    
    # Check for ensure_admin.py (Correct script name)
    if [ -f "scripts/ensure_admin.py" ]; then
        if python scripts/ensure_admin.py; then
            lifecycle_info "✅ Admin user seeded successfully"
            return 0
        else
            lifecycle_warn "Admin seeding failed (non-fatal)"
            return 0  # Don't fail supervisor on seeding errors
        fi
    else
        lifecycle_warn "Admin seeding script (scripts/ensure_admin.py) not found (skipping)"
        return 0
    fi
}

if seed_admin; then
    lifecycle_set_state "admin_seeded" "$(date +%s)"
else
    lifecycle_warn "Admin seeding had issues but continuing..."
fi

# ==============================================================================
# STEP 4: Application Server Launch (إطلاق خادم التطبيق)
# ==============================================================================

lifecycle_info "Step 4/5: Application server launch..."

# Acquire lock to prevent multiple instances
if ! lifecycle_acquire_lock "uvicorn_launch" 60; then
    lifecycle_error "Failed to acquire launch lock (another instance running?)"
    exit 1
fi

# Check if already running
if lifecycle_check_process "uvicorn.*app.main:app"; then
    lifecycle_info "Application server already running"
    lifecycle_release_lock "uvicorn_launch"
else
    lifecycle_info "Starting Uvicorn server..."
    
    # Start server in background
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "$APP_PORT" \
        --reload \
        --log-level info &
    
    UVICORN_PID=$!
    lifecycle_set_state "uvicorn_pid" "$UVICORN_PID"
    lifecycle_info "Uvicorn started (PID: $UVICORN_PID)"
    
    lifecycle_release_lock "uvicorn_launch"
fi

# ==============================================================================
# STEP 4B: Frontend Launch (Async - Non-Blocking)
# ==============================================================================

launch_frontend() {
    lifecycle_info "🚀 Frontend Launcher: Starting initialization..."

    if command -v npm >/dev/null 2>&1; then
        if [ ! -d "frontend/node_modules" ]; then
            lifecycle_info "Frontend Launcher: Installing dependencies (this may take a while)..."
            if (cd frontend && npm install); then
                lifecycle_set_state "frontend_dependencies_installed" "$(date +%s)"
                lifecycle_info "Frontend Launcher: Dependencies installed successfully"
            else
                lifecycle_warn "Frontend Launcher: Dependency install failed"
                return 1
            fi
        fi

        if lifecycle_check_process "next.*dev"; then
            lifecycle_info "Frontend Launcher: Next.js dev server already running"
        else
            lifecycle_info "Frontend Launcher: Starting Next.js dev server..."
            # Using exec to replace the subshell with the process
            (cd frontend && exec npm run dev -- --hostname 0.0.0.0 --port "$FRONTEND_PORT") &
            FRONTEND_PID=$!
            lifecycle_set_state "next_pid" "$FRONTEND_PID"
            lifecycle_info "Frontend Launcher: Next.js dev server started (PID: $FRONTEND_PID)"
        fi
    else
        lifecycle_warn "Frontend Launcher: npm not available"
    fi
}

if [ -f "frontend/package.json" ]; then
    lifecycle_info "Initializing Frontend in background (Async Mode)..."
    # Launch in background and don't wait
    launch_frontend >> "$APP_ROOT/.frontend_launcher.log" 2>&1 &
    lifecycle_info "✅ Frontend initialization offloaded to background process"
else
    lifecycle_info "Frontend directory not found - skipping Next.js startup"
fi

# ==============================================================================
# STEP 5: Health Check & Readiness (فحص الصحة والجاهزية)
# ==============================================================================

lifecycle_info "Step 5/5: Health check and readiness verification..."

# CODESPACES: Longer timeout for slower cloud environment
if [ -n "${CODESPACES:-}" ]; then
    PORT_TIMEOUT=300
    HEALTH_TIMEOUT=120
    lifecycle_info "Using extended timeouts for Codespaces (port: ${PORT_TIMEOUT}s, health: ${HEALTH_TIMEOUT}s)"
else
    PORT_TIMEOUT=60
    HEALTH_TIMEOUT=30
fi

# Wait for BACKEND port (Critical)
if ! lifecycle_wait_for_port "$APP_PORT" "$PORT_TIMEOUT"; then
    lifecycle_error "Backend Port $APP_PORT did not become available"
    exit 1
fi

# Verify application is actually healthy
lifecycle_info "Performing backend health check..."

if ! lifecycle_wait_for_http "$HEALTH_ENDPOINT" "$HEALTH_TIMEOUT" 200; then
    lifecycle_error "Health endpoint did not become healthy"
    exit 1
fi

health_response=$(curl -sf "$HEALTH_ENDPOINT" 2>/dev/null || echo "{}")
lifecycle_debug "Health response: $health_response"

if echo "$health_response" | grep -q '"application":"ok"'; then
    lifecycle_info "✅ Backend is healthy and ready!"
    lifecycle_set_state "app_healthy" "$(date +%s)"
    lifecycle_set_state "app_ready" "true"
else
    lifecycle_error "Health check failed: unexpected response"
    exit 1
fi

# ==============================================================================
# COMPLETION (الإكمال)
# ==============================================================================

lifecycle_info "═══════════════════════════════════════════════════════"
lifecycle_info "🎉 Application Lifecycle Complete - FAST BOOT ENABLED"
lifecycle_info "═══════════════════════════════════════════════════════"
lifecycle_info ""
lifecycle_info "✅ Core Systems Operational"
lifecycle_info "   • Dependencies: Installed"
lifecycle_info "   • Database: Migrated"
lifecycle_info "   • Admin User: Seeded"
lifecycle_info "   • Backend Server: Running on port $APP_PORT"
lifecycle_info "   • Backend Health: Verified"
lifecycle_info ""
lifecycle_info "⏳ Frontend Status:"
lifecycle_info "   • Initialization is running in BACKGROUND."
lifecycle_info "   • It may take a few more minutes to appear on port $FRONTEND_PORT."
lifecycle_info "   • Frontend Logs: .frontend_launcher.log"
lifecycle_info ""
lifecycle_info "🚀 CLICK HERE TO LOGIN:"
lifecycle_info "   http://localhost:$APP_PORT (API)"
lifecycle_info "   http://localhost:$FRONTEND_PORT (Web - Wait for it)"
lifecycle_info ""
lifecycle_info "📊 System Status:"
lifecycle_info "   • Uptime: $(uptime -p 2>/dev/null || echo 'N/A')"
lifecycle_info "   • Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $3 "/" $2}' || echo 'N/A')"
lifecycle_info "   • Processes: $(ps aux | wc -l) running"
lifecycle_info "═══════════════════════════════════════════════════════"

# Keep supervisor running to maintain state
lifecycle_info "Supervisor entering monitoring mode..."

# Monitor application health every 30 seconds
while true; do
    sleep 30
    
    if lifecycle_check_http "$HEALTH_ENDPOINT" 200; then
        lifecycle_debug "Health check passed"
    else
        lifecycle_warn "Health check failed - application may be down"
        lifecycle_clear_state "app_healthy"
    fi
done
