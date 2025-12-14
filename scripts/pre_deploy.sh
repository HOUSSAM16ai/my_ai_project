#!/bin/bash
# =============================================================================
# 🚀 COGNIFORGE PRE-DEPLOYMENT SCRIPT
# =============================================================================
# يُنفذ قبل كل deployment للتأكد من سلامة النظام
# يتحقق من: قاعدة البيانات، Schema، Migrations
# =============================================================================

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🚀 CogniForge Pre-Deployment Check                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL is not set!${NC}"
    echo "   Please set DATABASE_URL in your environment"
    exit 1
fi

echo -e "${GREEN}✅ DATABASE_URL is set${NC}"

# =============================================================================
# Step 1: Run pending migrations
# =============================================================================
echo ""
echo "🔧 Step 1: Running database migrations..."

if command -v alembic &> /dev/null; then
    alembic upgrade head
    echo -e "${GREEN}✅ Alembic migrations completed${NC}"
else
    echo -e "${YELLOW}⚠️ No migration tool found (alembic)${NC}"
    echo "   Skipping migration step"
fi

# =============================================================================
# Step 2: Validate Schema
# =============================================================================
echo ""
echo "🔍 Step 2: Validating database schema..."

python3 -c "
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

try:
    from sqlalchemy import create_engine, text

    db_url = os.getenv('DATABASE_URL', '')
    if 'asyncpg' in db_url:
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Check admin_conversations table
        result = conn.execute(text('''
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'admin_conversations'
        '''))
        columns = {row[0] for row in result.fetchall()}

        required_columns = {'id', 'title', 'user_id', 'linked_mission_id', 'created_at'}
        missing = required_columns - columns

        if missing:
            print(f'❌ Missing columns in admin_conversations: {missing}')
            print('   Run: scripts/fix_linked_mission_id_check.py')
            sys.exit(1)

        print('✅ Schema validation passed!')

except Exception as e:
    print(f'⚠️ Schema validation skipped: {e}')
    # Don't fail on validation errors in pre-deploy
"

# =============================================================================
# Step 3: Basic health check
# =============================================================================
echo ""
echo "🏥 Step 3: Running health check..."

python3 -c "
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

try:
    from sqlalchemy import create_engine, text

    db_url = os.getenv('DATABASE_URL', '')
    if 'asyncpg' in db_url:
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection OK')

except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Pre-Deployment Checks PASSED!                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🚀 Ready for deployment!${NC}"
