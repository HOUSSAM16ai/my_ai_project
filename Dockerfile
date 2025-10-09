# Dockerfile - Version 8.0 (The Dual-Authority Protocol)

# --- المرحلة الأولى: الورشة (Builder Stage) ---
FROM python:3.12-bullseye AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --extra-index-url https://download.pytorch.org/whl/cpu --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- المرحلة الثانية: صالة العرض (Final Stage) ---
FROM python:3.12-bullseye
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# --- [THE DUAL-AUTHORITY FIX] ---
# 1. تثبيت gosu، الأداة التي تسمح لنا بإسقاط الصلاحيات بأمان.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    bash \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# 2. إضافة مسار المستخدم إلى PATH. لا يزال هذا مهمًا لكي تجد الحاوية أوامر flask.
ENV PATH="/home/appuser/.local/bin:${PATH}"

# 3. إنشاء المستخدم والمجموعة.
RUN addgroup --system appgroup && adduser --system --group appuser

# 4. نسخ وتثبيت كل شيء كـ root.
WORKDIR /app
COPY --from=builder /app/wheels /wheels
# يجب تشغيل pip كـ root حتى يتمكن من الكتابة في المجلدات العامة.
RUN pip install --no-cache-dir --no-index /wheels/*
COPY . .
# --- نهاية الإصلاح ---
    
EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]