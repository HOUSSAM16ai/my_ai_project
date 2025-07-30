# Dockerfile - Version 7.0 (Multi-stage Build with Full Bullseye)
# This represents the pinnacle of professional setup for a complex project.

# --- المرحلة الأولى: الورشة (Builder Stage) ---
# نستخدم صورة Bullseye كاملة ونسميها 'builder'.
# هذه المرحلة تحتوي على كل الأدوات الثقيلة اللازمة لبناء وترجمة مكتبات بايثون.
FROM python:3.12-bullseye AS builder

# إعدادات البيئة الأساسية
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# تثبيت أدوات البناء الأساسية فقط في هذه المرحلة
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# هذه هي الخطوة السحرية: نقوم ببناء "عجلات" (wheels) لكل الاعتماديات.
# هذا يقوم بترجمة أي كود C مسبقًا ويجهز الحزم للتثبيت السريع في المرحلة النهائية.
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# --- المرحلة الثانية: صالة العرض (Final Stage) ---
# نبدأ من جديد بصورة Bullseye نظيفة. هذه هي الصورة النهائية التي سيتم نشرها.
FROM python:3.12-bullseye

# إعدادات البيئة الأساسية
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# تثبيت فقط ما هو ضروري لتشغيل التطبيق (وليس بنائه)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    netcat-traditional \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# إنشاء المستخدم الآمن الذي سيعمل به التطبيق
RUN addgroup --system appgroup && adduser --system --group appuser

# نسخ العجلات المبنية مسبقًا من "الورشة" وتثبيتها
# هذه العملية سريعة جدًا لأنها لا تحتاج إلى ترجمة
COPY --from=builder /app/wheels /wheels
# نستخدم --no-index لمنع pip من البحث في الإنترنت، مما يضمن استخدام العجلات المحلية فقط
RUN pip install --no-cache-dir --no-index /wheels/*

# نسخ كود التطبيق
COPY . .
    
# إعداد المنفذ ونقطة الدخول النهائية
EXPOSE 5000
# سيتم تشغيل هذا السكربت بصلاحيات root، وسيقوم Gunicorn في النهاية بإسقاط الصلاحيات
ENTRYPOINT ["/app/entrypoint.sh"]