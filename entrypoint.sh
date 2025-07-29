#!/bin/sh
# entrypoint.sh - Final Professional Version
# Exit immediately if a command exits with a non-zero status.
set -e

# هذا السكربت يعمل الآن بالكامل بصلاحيات root، مما يسمح له بإنشاء الملفات.

# --- 1. انتظار قاعدة البيانات ---
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started!"

# --- 2. تحديد تطبيق Flask ---
export FLASK_APP=cogniforge.py

# --- 3. تهيئة وترقية قاعدة البيانات (تُنفذ كـ root) ---
echo "Initializing database migrations (if needed)..."
# التحقق من وجود مجلد migrations. إذا لم يكن موجودًا، قم بإنشائه.
if [ ! -d "migrations" ]; then
    flask db init
    flask db migrate -m "Initial database structure"
    echo "Migrations directory created."
fi

echo "Running database upgrades..."
flask db upgrade
echo "Database is up to date."

# --- 4. إضافة البيانات الأولية (تُنفذ كـ root) ---
echo "Seeding database with initial data..."
flask seed-db
echo "Seeding complete."

# --- 5. تشغيل الخادم مع إسقاط الصلاحيات (الأهم) ---
# نستخدم خيارات Gunicorn لتشغيل التطبيق بالمستخدم والمجموعة المحددين.
# هذا هو النمط الآمن والاحترافي.
echo "Starting Gunicorn server as non-root user 'appuser'..."
exec gunicorn --workers 1 --bind 0.0.0.0:5000 --user appuser --group appgroup --reload "app:create_app()"