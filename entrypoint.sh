#!/bin/sh
# entrypoint.sh - v9.3 (The Dual-Authority Protocol)
set -e

# --- المرحلة الأولى: مرحلة السلطة العليا (تنفيذ كـ root) ---
# يتم تشغيل هذا الجزء من السكربت بواسطة root بشكل افتراضي.

echo ">>> [ROOT] Ensuring runtime directories and permissions..."

# 1. نقوم بإنشاء المجلدات الضرورية في وقت التشغيل.
mkdir -p /app/tmp /home/appuser/.cache/huggingface

# 2. نقوم بتغيير ملكية كل شيء لضمان أن appuser يمكنه العمل.
#    هذا يصلح أي مشاكل ناتجة عن ربط المجلدات (volume mounting).
chown -R appuser:appgroup /app /home/appuser/.cache

# --- المرحلة الثانية: مرحلة تسليم السلطة (تنفيذ كـ appuser) ---
# نستخدم 'exec gosu appuser "$@"' لتشغيل بقية الأمر
# (وهو gunicorn run:app $GUNICORN_CMD_ARGS) بصلاحيات المستخدم الآمن 'appuser'.
echo ">>> [ROOT] Dropping privileges and handing over control to appuser..."
exec gosu appuser "$@"