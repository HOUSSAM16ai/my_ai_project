# Dockerfile - Version 7.2 (The Final Permission Protocol)

# --- المرحلة الأولى: الورشة (Builder Stage) ---
FROM python:3.12-bullseye AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- المرحلة الثانية: صالة العرض (Final Stage) ---
FROM python:3.12-bullseye
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev netcat-traditional bash \
    && rm -rf /var/lib/apt/lists/*

# --- [THE SUPERCHARGED PERMISSION PROTOCOL] ---
# 1. إنشاء المستخدم والمجموعة الآمنة
RUN addgroup --system appgroup && adduser --system --group appuser

# 2. إنشاء وتخصيص المجلدات الحيوية **قبل** تبديل المستخدم
#    هذا يضمن أن root هو من ينشئها، ثم يعطي الملكية لـ appuser.
WORKDIR /app
RUN mkdir -p /home/appuser/.cache/huggingface /app/tmp \
    && chown -R appuser:appgroup /home/appuser/.cache /app/tmp

# 3. تبديل المستخدم إلى المستخدم الآمن **قبل** تثبيت أي شيء
USER appuser

# 4. الآن، كـ appuser، نقوم بنسخ وتثبيت الكود
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-index /wheels/*
COPY . .
# --- نهاية بروتوكول الأذونات ---

# --- [GUNICORN FIX] ---
# إخبار Gunicorn باستخدام المجلد المؤقت الآمن الذي أنشأناه
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:5000 --worker-tmp-dir /app/tmp"
# --- نهاية الإصلاح ---
    
EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]