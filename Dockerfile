# Dockerfile - Version 4.0 (Final & Corrected)
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk update && \
    apk add --no-cache --virtual .build-deps build-base postgresql-dev && \
    apk add --no-cache postgresql-client netcat-openbsd bash && \
    pip install --no-cache-dir gunicorn && \
    apk del .build-deps

WORKDIR /app

# إنشاء المجموعة والمستخدم، لكن لا نستخدمه الآن
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --- هذا السطر لم نعد بحاجة إليه، لقد تسبب في مشاكل الصلاحيات ---
# RUN chown -R appuser:appgroup /app

# --- هذا هو السطر الأهم الذي سنقوم بحذفه أو التعليق عليه ---
# USER appuser

EXPOSE 5000

# سيتم تشغيل هذا السكربت الآن بصلاحيات root
ENTRYPOINT ["/app/entrypoint.sh"]