#!/bin/bash
set -e
echo "
🧠 On-Attach: Synchronizing runtime state...
"
# الانتظار للتأكد من أن قاعدة البيانات جاهزة تمامًا
echo "Waiting for database to be healthy..."
# (ملاحظة: هذا يتطلب أن تكون خدمة web لديها netcat أو أداة مشابهة)
# يمكننا استخدام حلقة بسيطة كبديل
while ! docker-compose exec -T db pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-cogniforge_db} > /dev/null 2>&1; do
    sleep 1
done
echo "Database is ready."

# الآن نقوم بتشغيل الهجرة
echo "Running database migrations..."
flask db upgrade

# رسالة الترحيب النهائية
echo "
🌟 Environment Ready. Happy Forging!
"