#!/usr/bin/env bash
###############################################################################
# Cleanup Large Artifacts
#
# Removes generated, heavyweight folders that should never be committed and
# are safe to regenerate (dependencies, build outputs, caches).
###############################################################################

set -Eeuo pipefail

readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

readonly TARGET_DIRS=(
  "node_modules"
  "frontend/node_modules"
  "frontend/.next"
  "frontend/out"
  "frontend/.turbo"
  "frontend/.cache"
  "frontend/dist"
  "frontend/build"
  "app/static/dist"
  "app/static/build"
  ".pytest_cache"
  ".mypy_cache"
  ".ruff_cache"
  ".cache"
  ".turbo"
)

echo "🧹 Cleaning large generated artifacts..."

for relative_path in "${TARGET_DIRS[@]}"; do
  absolute_path="${PROJECT_ROOT}/${relative_path}"
  if [ -e "$absolute_path" ]; then
    echo " - Removing ${relative_path}"
    rm -rf "$absolute_path"
  fi
done

echo "✅ Cleanup complete."
