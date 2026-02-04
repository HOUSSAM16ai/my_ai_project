#!/bin/bash
# Auto-generated fix script
# Run this to fix detected code quality issues

echo "🚀 Fixing code quality issues..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


echo "⚡ Auto-fixing Ruff issues..."
ruff check --fix app/ tests/

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Fixes applied! Please review and commit changes."
