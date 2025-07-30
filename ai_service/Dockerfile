# Dockerfile for AI Service - Version 1.1 (Corrected PATH)
FROM python:3.12-bullseye

# إعدادات البيئة الأساسية
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- التعديل الأول: إضافة مسار تثبيت pip إلى PATH ---
# هذا يضمن أن النظام يمكنه العثور على أي برامج يتم تثبيتها بواسطة pip.
ENV PATH="/root/.local/bin:${PATH}"
    
WORKDIR /code

# نسخ وتثبيت الاعتماديات
COPY ./requirements.txt /code/requirements.txt
# --- التعديل الثاني: تحديث pip أولاً لضمان أفضل توافق ---
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

# نسخ باقي كود التطبيق
COPY ./ /code/
    
# كشف المنفذ الذي سيعمل عليه الخادم
EXPOSE 8000
    
# الأمر لتشغيل الخادم
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]