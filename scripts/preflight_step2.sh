#!/bin/bash
# scripts/preflight_step2.sh
#
# Preflight check script for the Reality Kernel v2 migration.
# This script verifies that the environment is ready for the migration process.

echo "--- Starting Step 2 Preflight Checks ---"

# 1. Verify Python Version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$PYTHON_VERSION" != "3.12" ]]; then
    echo "FAIL: Incorrect Python version. Expected 3.12, but found $PYTHON_VERSION."
    exit 1
fi
echo "OK ($PYTHON_VERSION)"

# 2. Verify Critical Dependencies are installed
echo -n "Checking for fastapi... "
python -c "import fastapi" &> /dev/null
if [ $? -ne 0 ]; then
    echo "FAIL: fastapi is not installed."
    exit 1
fi
echo "OK"

echo -n "Checking for sqlalchemy... "
python -c "import sqlalchemy" &> /dev/null
if [ $? -ne 0 ]; then
    echo "FAIL: sqlalchemy is not installed."
    exit 1
fi
echo "OK"

echo -n "Checking for pydantic... "
python -c "import pydantic" &> /dev/null
if [ $? -ne 0 ]; then
    echo "FAIL: pydantic is not installed."
    exit 1
fi
echo "OK"

# 3. Verify Reality Kernel v2 files exist
echo -n "Checking for Reality Kernel v2 core files... "
if [ ! -f "app/core/kernel_v2/meta_kernel.py" ]; then
    echo "FAIL: meta_kernel.py is missing."
    exit 1
fi
echo "OK"


echo "--- Preflight Checks Passed Successfully ---"
exit 0
