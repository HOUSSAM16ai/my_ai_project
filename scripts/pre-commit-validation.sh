#!/bin/bash

# 🛡️ Pre-Commit Structure Validation Hook
# This script prevents committing code with structure errors

set -e

echo "🔍 Running structure validation..."

# Run structure validation
if ! python scripts/validate_structure.py; then
    echo ""
    echo "❌ COMMIT BLOCKED: Structure validation failed!"
    echo ""
    echo "The following issues were found:"
    echo "  - Methods defined outside their classes"
    echo "  - Incorrect indentation in service files"
    echo ""
    echo "Please fix the errors above before committing."
    echo "See PREVENTION_GUIDE.md for help."
    echo ""
    exit 1
fi

echo "✅ Structure validation passed!"
echo ""

# Run critical tests
echo "🧪 Running critical service method tests..."
if ! python -m pytest tests/integration/test_chat_e2e.py::TestServiceMethodsAccessibility -q; then
    echo ""
    echo "❌ COMMIT BLOCKED: Critical tests failed!"
    echo ""
    echo "Service methods are not accessible correctly."
    echo "This could cause AttributeError in production."
    echo ""
    echo "Please fix the issues above before committing."
    echo ""
    exit 1
fi

echo "✅ All critical tests passed!"
echo ""
echo "✅ Ready to commit!"
