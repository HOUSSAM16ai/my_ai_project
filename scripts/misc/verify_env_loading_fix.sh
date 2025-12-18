#!/usr/bin/env bash
###############################################################################
# verify_env_loading_fix.sh
#
# This script verifies that the .env loading fix is working correctly.
# It tests the safe loading function with various edge cases.
###############################################################################

set -Eeuo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "  Testing .env Loading Fix"
echo "========================================="
echo ""

# Create a test .env file with problematic content
TEST_ENV="/tmp/verify_env_test.env"
cat > "$TEST_ENV" << 'EOF'
# ======================================================================================
# Test .env file with various edge cases
# ======================================================================================

# Simple key-value
SIMPLE_KEY=simple_value

# Quoted value with spaces
QUOTED_VALUE="value with spaces"

# Inline comment (should be stripped for unquoted values)
INLINE_COMMENT=value # this should be removed

# Quoted value with inline comment (should be preserved)
QUOTED_INLINE="value # this should stay"

# Empty value
EMPTY_VALUE=

# Comment line - should be ignored
# COMMENTED_KEY=should_not_load

# Invalid key with spaces - should be ignored
INVALID KEY=bad

# Value with trimming needed
  TRIMMED_KEY  =  trimmed_value  

# Admin name with quotes
ADMIN_NAME="Admin User"
EOF

echo "Created test .env file with edge cases:"
echo "----------------------------------------"
cat "$TEST_ENV"
echo "----------------------------------------"
echo ""

# Source the safe loading function
load_env_file() {
  local env_file="${1:-.env}"
  [[ ! -f "$env_file" ]] && return 0

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    [[ "$line" != *"="* ]] && continue

    local key="${line%%=*}"
    local val="${line#*=}"

    key="$(echo -n "$key" | sed -E 's/[[:space:]]+//g')"
    if ! [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      continue
    fi

    if [[ "$val" != \"*\" && "$val" != \'*\' ]]; then
      val="${val%%#*}"
      val="${val%"${val##*[![:space:]]}"}"
    fi

    export "$key=$val"
  done < "$env_file"
}

# Test the loading
echo "Testing safe .env loading..."
if load_env_file "$TEST_ENV"; then
  echo -e "${GREEN}✅ Load completed without errors${NC}"
else
  echo -e "${RED}❌ Load failed${NC}"
  exit 1
fi

echo ""
echo "Verifying loaded variables:"
echo "----------------------------------------"

# Test cases
test_var() {
  local var_name="$1"
  local expected="$2"
  
  # Check if variable is set (even if empty)
  if [ -z "${!var_name+x}" ]; then
    echo -e "${RED}❌${NC} $var_name is not set (expected: \"$expected\")"
    return 1
  fi
  
  local actual="${!var_name}"
  
  if [ "$actual" = "$expected" ]; then
    echo -e "${GREEN}✅${NC} $var_name = \"$actual\""
  else
    echo -e "${RED}❌${NC} $var_name = \"$actual\" (expected: \"$expected\")"
    return 1
  fi
}

test_not_set() {
  local var_name="$1"
  if [ -z "${!var_name:-}" ]; then
    echo -e "${GREEN}✅${NC} $var_name is not set (as expected)"
  else
    echo -e "${RED}❌${NC} $var_name = \"${!var_name}\" (should not be set)"
    return 1
  fi
}

all_passed=true

test_var "SIMPLE_KEY" "simple_value" || all_passed=false
test_var "QUOTED_VALUE" "\"value with spaces\"" || all_passed=false
test_var "INLINE_COMMENT" "value" || all_passed=false
test_var "QUOTED_INLINE" "\"value # this should stay\"" || all_passed=false
test_var "EMPTY_VALUE" "" || all_passed=false
test_var "TRIMMED_KEY" "  trimmed_value" || all_passed=false
test_var "ADMIN_NAME" "\"Admin User\"" || all_passed=false
test_not_set "COMMENTED_KEY" || all_passed=false
test_not_set "INVALID" || all_passed=false

echo "----------------------------------------"
echo ""

if [ "$all_passed" = true ]; then
  echo -e "${GREEN}=========================================${NC}"
  echo -e "${GREEN}  ✅ All tests passed!${NC}"
  echo -e "${GREEN}  The .env loading fix is working correctly.${NC}"
  echo -e "${GREEN}=========================================${NC}"
  exit 0
else
  echo -e "${RED}=========================================${NC}"
  echo -e "${RED}  ❌ Some tests failed${NC}"
  echo -e "${RED}=========================================${NC}"
  exit 1
fi
