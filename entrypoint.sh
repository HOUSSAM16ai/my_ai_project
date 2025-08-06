#!/bin/sh
# entrypoint.sh - v7.0 (Pure Ignition)
set -e
# All database tasks are now definitively handled by the 'migrations' service.
echo ">>> [WEB Entrypoint] Database is built. Igniting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --user appuser --group appgroup "run:app"
```*   **لماذا؟** نحن نزيل كل مسؤولية بناء قاعدة البيانات من هذا الملف.

---

#### **3. ملف `./ai_service/entrypoint.sh` (الخاص بـ FastAPI - المبسط)**

**امسح كل محتوى `./ai_service/entrypoint.sh` واستبدله بهذا الكود:**
```bash
#!/bin/sh
# ai_service/entrypoint.sh - v4.0 (Trusts the Orchestrator)
set -e
# The 'migrations' service guarantees the world is built before we start.
echo ">>> [AI Core] The world is built. Igniting Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000