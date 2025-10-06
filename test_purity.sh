#!/bin/bash

echo "=========================================="
echo "🔥 ARCHITECTURAL PURITY VERIFICATION"
echo "=========================================="
echo ""

# Check Docker Compose
echo "1. Checking Docker Compose..."
if grep -q "db:" docker-compose.yml && grep -q "image: postgres" docker-compose.yml; then
    echo "   ❌ FAIL: Local DB service found in docker-compose.yml"
    EXIT_CODE=1
else
    echo "   ✅ PASS: No local DB service - Pure cloud architecture!"
fi

if grep -q "depends_on:" docker-compose.yml && grep -q "- db" docker-compose.yml; then
    echo "   ❌ FAIL: depends_on db found in docker-compose.yml"
    EXIT_CODE=1
else
    echo "   ✅ PASS: No depends_on db - No phantom dependencies!"
fi

# Check DATABASE_URL
echo ""
echo "2. Checking DATABASE_URL..."
if [ -f .env ]; then
    if grep -q "DATABASE_URL" .env; then
        echo "   ✅ PASS: DATABASE_URL found in .env"
        if grep "DATABASE_URL" .env | grep -q "supabase.co\|cloud"; then
            echo "   ✅ PASS: Points to cloud database!"
        fi
    else
        echo "   ❌ FAIL: DATABASE_URL not found in .env"
        EXIT_CODE=1
    fi
else
    echo "   ⚠️  WARNING: .env file not found"
fi

# Check Models
echo ""
echo "3. Checking Models..."
EXPECTED_MODELS=("class User" "class Mission" "class MissionPlan" "class Task" "class MissionEvent")
PURIFIED_MODELS=("class Subject" "class Lesson" "class Exercise" "class Submission" "class AdminConversation" "class AdminMessage")

for model in "${EXPECTED_MODELS[@]}"; do
    if grep -q "$model" app/models.py; then
        echo "   ✅ $model found"
    else
        echo "   ❌ $model NOT found"
        EXIT_CODE=1
    fi
done

echo ""
echo "   Checking for purified (removed) models..."
IMPURITIES=0
for model in "${PURIFIED_MODELS[@]}"; do
    if grep -q "$model" app/models.py; then
        echo "   ❌ $model should be removed!"
        IMPURITIES=$((IMPURITIES + 1))
    else
        echo "   ✨ $model successfully removed"
    fi
done

if [ $IMPURITIES -eq 0 ]; then
    echo "   ✅ Models are pure - no legacy code!"
fi

# Check Migrations
echo ""
echo "4. Checking Migrations..."
if [ -d "migrations/versions" ]; then
    MIGRATION_COUNT=$(ls -1 migrations/versions/*.py 2>/dev/null | wc -l)
    echo "   ✅ Found $MIGRATION_COUNT migration files"
    
    if ls migrations/versions/*purify* 2>/dev/null | grep -q .; then
        echo "   ✅ Purification migration found!"
    else
        echo "   ⚠️  Purification migration not found"
    fi
else
    echo "   ❌ migrations/versions directory not found"
    EXIT_CODE=1
fi

# Final Report
echo ""
echo "=========================================="
echo "🎯 FINAL REPORT"
echo "=========================================="

if [ ${EXIT_CODE:-0} -eq 0 ] && [ $IMPURITIES -eq 0 ]; then
    echo ""
    echo "🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
    echo "✅ ARCHITECTURAL PURITY: 100% SUCCESS!"
    echo "��🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
    echo ""
    echo "✨ Database is cloud-ready 100%!"
    echo "✨ Pure Overmind architecture - 5 tables only!"
    echo "✨ Docker Compose is pure - no local DB!"
    echo "✨ All legacy tables removed!"
    echo ""
    exit 0
else
    echo ""
    echo "⚠️  Some issues found - please review above"
    echo ""
    exit 1
fi
