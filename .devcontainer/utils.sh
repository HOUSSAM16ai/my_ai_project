#!/usr/bin/env bash

# This script is meant to be sourced by other scripts to provide common utility functions.

# Colors for output
if [ -t 1 ]; then
  RED=$(printf '\\033[31m'); GREEN=$(printf '\\033[32m'); YELLOW=$(printf '\\033[33m')
  CYAN=$(printf '\\033[36m'); BOLD=$(printf '\\033[1m'); RESET=$(printf '\\033[0m')
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

log()  { printf "%s[INFO]%s %s\\n"  "$CYAN"  "$RESET" "$1"; }
ok()   { printf "%s[ OK ]%s %s\\n"  "$GREEN" "$RESET" "$1"; }
warn() { printf "%s[WARN]%s %s\\n"  "$YELLOW" "$RESET" "$1"; }
err()  { printf "%s[ERR ]%s %s\\n"  "$RED"   "$RESET" "$1" >&2; }

# Function to safely load environment variables from a file if they are not already set
load_env_file_if_needed() {
  if [[ -n "${DATABASE_URL:-}" && -n "${OPENROUTER_API_KEY:-}" ]]; then
    log "🔐 Using Codespaces Secrets (DATABASE_URL and OPENROUTER_API_KEY are set)"
    return 0
  fi

  local env_file="${1:-.env}"
  [[ ! -f "$env_file" ]] && return 0

  log "📄 Loading environment variables from $env_file"

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    if [[ -z "$line" || "${line:0:1}" == "#" || "$line" != *"="* ]]; then
      continue
    fi

    local key="${line%%=*}"
    local val="${line#*=}"
    key="$(echo -n "$key" | sed -E 's/[[:space:]]+//g')"

    if ! [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      continue
    fi

    if [[ "$val" != \\"*\\" && "$val" != \\'*\\' ]]; then
      val="${val%%#*}"
      val="${val%"${val##*[![:space:]]}"}"
    fi

    if [[ -z "${!key:-}" ]]; then
      export "$key=$val"
    fi
  done < "$env_file"
}
