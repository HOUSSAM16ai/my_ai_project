# Dockerfile for AI Service - using our new Bullseye standard
FROM python:3.12-bullseye

# إعدادات البيئة الأساسية
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# نسخ وتثبيت الاعتماديات أولاً للاستفادة من التخزين المؤقت
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# نسخ باقي كود التطبيق
COPY ./ /code/

# كشف المنفذ الذي سيعمل عليه الخادم
EXPOSE 8000

# الأمر لتشغيل الخادم
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]