# --- Alpine Based Dockerfile ---

# 1. استخدم صورة Python Alpine أساسية ومستقرة
FROM python:3.12-alpine

# 2. تعيين متغيرات البيئة الأساسية
#    PYTHONDONTWRITEBYTECODE يمنع إنشاء ملفات .pyc
#    PYTHONUNBUFFERED يضمن ظهور المخرجات مباشرة في السجلات
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. تثبيت التبعيات على مستوى النظام
#    build-base: ضروري لتجميع بعض مكتبات Python (مثل numpy, psycopg2)
#    postgresql-dev: ضروري لمكتبة psycopg2 للاتصال بـ PostgreSQL
#    git: ضروري للتحكم في الإصدار داخل الحاوية
RUN apk update && \
    apk add --no-cache build-base postgresql-dev git

# 4. تعيين مجلد العمل
WORKDIR /app

# 5. نسخ ملف متطلبات المكتبات أولاً للاستفادة من التخزين المؤقت
COPY requirements.txt .

# 6. تثبيت مكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# 7. نسخ باقي كود التطبيق
COPY . .

# 8. تعريض المنفذ (للتوثيق)
EXPOSE 5000

# 9. الأمر الافتراضي لتشغيل التطبيق باستخدام Gunicorn
#    استخدام worker واحد لتقليل استهلاك الذاكرة
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:create_app()"]

