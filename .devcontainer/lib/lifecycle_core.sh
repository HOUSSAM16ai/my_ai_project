#!/usr/bin/env bash
# lifecycle_core.sh - Core library for DevContainer lifecycle scripts

# Colors
export COLOR_RED=$(printf '\033[31m')
export COLOR_GREEN=$(printf '\033[32m')
export COLOR_YELLOW=$(printf '\033[33m')
export COLOR_CYAN=$(printf '\033[36m')
export COLOR_BLUE=$(printf '\033[34m')
export COLOR_RESET=$(printf '\033[0m')

# State Directory
readonly STATE_DIR=".devcontainer/state"
readonly LOCK_DIR=".devcontainer/locks"

# Ensure directories exist
mkdir -p "$STATE_DIR" "$LOCK_DIR"

lifecycle_info() {
    echo "${COLOR_CYAN}[INFO]${COLOR_RESET} $1"
}

lifecycle_error() {
    echo "${COLOR_RED}[ERROR]${COLOR_RESET} $1" >&2
}

lifecycle_warn() {
    echo "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

lifecycle_debug() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo "${COLOR_BLUE}[DEBUG]${COLOR_RESET} $1"
    fi
}

lifecycle_set_state() {
    local key="$1"
    local value="$2"
    echo "$value" > "$STATE_DIR/$key"
}

lifecycle_get_state() {
    local key="$1"
    if [ -f "$STATE_DIR/$key" ]; then
        cat "$STATE_DIR/$key"
    else
        echo ""
    fi
}

lifecycle_has_state() {
    local key="$1"
    [ -f "$STATE_DIR/$key" ]
}

lifecycle_clear_state() {
    local key="$1"
    rm -f "$STATE_DIR/$key"
}

lifecycle_check_http() {
    local url="$1"
    local expected_code="$2"
    local timeout="${3:-5}"

    if ! command -v curl >/dev/null 2>&1; then
        return 1
    fi

    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" || echo "000")

    if [ "$code" -eq "$expected_code" ]; then
        return 0
    else
        return 1
    fi
}

lifecycle_acquire_lock() {
    local lock_name="$1"
    local timeout="${2:-60}"
    local lock_file="$LOCK_DIR/$lock_name.lock"
    local start_time=$(date +%s)

    while [ -f "$lock_file" ]; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ "$elapsed" -ge "$timeout" ]; then
            # Check if process holding lock is still alive
            local pid=$(cat "$lock_file")
            if ! kill -0 "$pid" 2>/dev/null; then
                lifecycle_warn "Removing stale lock for $lock_name (PID $pid)"
                rm -f "$lock_file"
                break
            fi
            return 1
        fi
        sleep 1
    done

    echo "$$" > "$lock_file"
    return 0
}

lifecycle_release_lock() {
    local lock_name="$1"
    local lock_file="$LOCK_DIR/$lock_name.lock"

    if [ -f "$lock_file" ]; then
        # Only release if we own it
        if [ "$(cat "$lock_file")" = "$$" ]; then
            rm -f "$lock_file"
        fi
    fi
}

lifecycle_check_process() {
    local pattern="$1"
    pgrep -f "$pattern" >/dev/null 2>&1
}

lifecycle_wait_for_port() {
    local port="$1"
    local timeout="${2:-30}"
    local start_time=$(date +%s)

    # Use Python for port checking to avoid dependency on netcat (nc)
    while ! python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); s.connect(('localhost', $port))" >/dev/null 2>&1; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ "$elapsed" -ge "$timeout" ]; then
            return 1
        fi
        sleep 1
    done
    return 0
}

lifecycle_wait_for_http() {
    local url="$1"
    local timeout="${2:-30}"
    local expected_code="${3:-200}"
    local start_time=$(date +%s)

    while ! lifecycle_check_http "$url" "$expected_code" 1; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ "$elapsed" -ge "$timeout" ]; then
            return 1
        fi
        sleep 1
    done
    return 0
}
