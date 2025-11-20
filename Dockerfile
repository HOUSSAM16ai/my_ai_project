# Stage 1: Builder (تجهيز المكتبات)
FROM python:3.12-slim as builder

WORKDIR /app

# تحسينات الأداء: منع ملفات .pyc ومنع الكاش لتسريع البناء
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# تثبيت أدوات البناء الضرورية فقط
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Runtime (الصورة النهائية)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
# Ensure /app is in PYTHONPATH so absolute imports work
ENV PYTHONPATH="/app:$PYTHONPATH"

# --- الإضافة الحاسمة ---
# تثبيت أدوات النظام التي يحتاجها VS Code والـ Healthchecks
# إضافة libpq-dev لدعم psycopg2/asyncpg في وقت التشغيل
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    procps \
    iproute2 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم للتطبيق (للأمان في الإنتاج)
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . .

# منح الصلاحيات
RUN chown -R appuser:appuser /app

# ملاحظة: في الـ Dockerfile نحدد المستخدم الافتراضي
# ولكن في DevContainer سنتجاوزه لنستخدم root
USER appuser

# توحيد المنفذ عالمياً
EXPOSE 8000

CMD ["uvicorn", "app.main:root", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
