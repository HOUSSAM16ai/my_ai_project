#!/bin/bash
set -e
echo "
🧠 On-Attach: Synchronizing runtime state...
"
# الانتظار للتأكد من أن قاعدة البيانات جاهزة تمامًا
echo "Waiting for database to be healthy..."
# نستخدم حلقة بسيطة وآمنة للتحقق من جاهزية قاعدة البيانات
# تستخدم متغيرات البيئة الافتراضية إذا لم يتم تحديدها
while ! docker-compose exec -T db pg_isready -U ${POSTGRES_USER:-user} -d ${POSTGRES_DB:-mydb} > /dev/null 2>&1; do
    echo "   - Database is not ready yet, waiting..."
    sleep 2
done
echo "✅ Database is ready."

# الآن نقوم بتشغيل الهجرة
echo "Running database migrations..."
flask db upgrade

# --- [THE AUTOMATIC SEEDING PROTOCOL] ---
# الآن نقوم بتشغيل أمر تهيئة المشرف تلقائيًا
echo "🌱 Seeding initial data... Creating admin user if not exists."
flask users init-admin
# --- نهاية البروتوكول ---

# رسالة الترحيب النهائية
echo "
🌟 Environment Ready. Happy Forging!
"