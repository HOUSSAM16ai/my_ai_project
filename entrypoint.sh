#!/bin/sh
# entrypoint.sh - v9.1 (Environment-Aware Ignition Protocol)
set -e

# هذا السكربت لم يعد يتخذ قرارات، بل ينفذ الأوامر من البيئة.
# Gunicorn سيبدأ بالإعدادات المعرفة في متغير GUNICORN_CMD_ARGS
# داخل الـ Dockerfile، مما يضمن استخدام --worker-tmp-dir الصحيح.

echo ">>> [WEB Entrypoint] Environment configured. Igniting Gunicorn..."
exec gunicorn "run:app" $GUNICORN_CMD_ARGS