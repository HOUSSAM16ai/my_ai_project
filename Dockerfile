# المرحلة الأولى: builder - لبناء التبعيات
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# المرحلة الثانية: final - الصورة النهائية للتشغيل والتطوير
FROM python:3.12-slim-bookworm AS final

# تثبيت sudo و git
RUN apt-get update && apt-get install -y --no-install-recommends sudo git && rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم 'appuser' وإضافته إلى مجموعة sudo دون الحاجة لكلمة مرور
RUN useradd -m -s /bin/bash appuser && \
    echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# نسخ البيئة الافتراضية
COPY --from=builder /opt/venv /opt/venv

# نسخ كود التطبيق
COPY . .

# تغيير ملكية مجلد التطبيق إلى appuser
RUN chown -R appuser:appuser /app

# تفعيل البيئة الافتراضية
ENV PATH="/opt/venv/bin:$PATH"

# التبديل إلى المستخدم appuser
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]


