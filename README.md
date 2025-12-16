# 🌟 CogniForge - The Superior AI-Powered Educational Platform

> **نظام تعليمي ذكي خارق مدعوم بالذكاء الاصطناعي**

> **🔥 REALITY KERNEL V3 ARCHITECTURE** → The project is now powered by a framework-agnostic, hyper-modular, self-healing architecture.

---

## 🚀 Overview | نظرة عامة

CogniForge is an advanced, AI-powered educational platform built on a next-generation system where Reality Kernel v3 is the central execution spine. All APIs are built in a fully framework-agnostic, hyper-modular architecture.

---

## 🎯 Quick Start | البدء السريع

### 1️⃣ Automated Setup & Run (Superhuman Environment) | الإعداد والتشغيل الآلي الخارق

To get started, simply run the robust development setup script. This **"Superhuman Setup"** handles the entire lifecycle with zero friction:

1.  **Dependencies:** Automatically verifies and installs Python packages.
2.  **Configuration:** Auto-generates a secure `.env` file if missing (or respects existing secrets).
3.  **Codespaces Automation:** **Automatically enforces "Public" visibility** for Port 8000, ensuring the browser opens instantly without "White Page" errors.
4.  **Auto-Healing:** Kills stale processes locking the port and runs the server in an **auto-restart loop** (crash-proof).

```bash
# Make the script executable (only needs to be done once)
chmod +x scripts/setup_dev.sh

# Run the Superhuman Setup script
./scripts/setup_dev.sh
```

The application will be automatically exposed at `http://localhost:8000` (or your Codespace URL).

### ❗️ Automated Port Visibility (Codespaces)

The new setup script (`scripts/setup_dev.sh`) explicitly runs `gh codespace ports visibility 8000:public`. This ensures that the environment transition is seamless and the "Open in Browser" notification appears immediately.

- **Manual Verification (Fallback):** If for some reason the automation fails, go to the **PORTS** tab and ensure port 8000 is **Public**.

### Codespaces / Preview Troubleshooting

If you see a **White Page** or blank screen in the Codespaces preview, but the `/health` endpoint is working:
1.  Ensure you are in a dev environment (`ENVIRONMENT=development` or running inside Codespaces).
2.  Run the verification script to check for header issues:
    ```bash
    ./scripts/codespace_guardian.sh
    ```
    This script verifies that the security headers blocking iframe embedding (`X-Frame-Options`, `Content-Security-Policy: frame-ancestors`) are correctly relaxed for the preview environment.

**How it works:**
The application includes a development-only middleware (`app/middleware/remove_blocking_headers.py`) that:
*   Removes `X-Frame-Options`.
*   Relaxes `Content-Security-Policy` by removing `frame-ancestors`.

This allows the application to be embedded in the Codespaces preview iframe. **This relaxation is strictly disabled in production.**

**Rollback:**
To disable this behavior, set `ENVIRONMENT=production` or remove `RemoveBlockingHeadersMiddleware` from `app/main.py`.

### 2️⃣ Manual Setup (For Advanced Users) | الإعداد اليدوي

If you prefer to set up the environment manually, follow these steps:

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    npm install
    ```
2.  **Configure Environment:**
    -   Copy `.env.example` to `.env`.
    -   Update `DATABASE_URL` and other critical variables.
3.  **Build Frontend:**
    ```bash
    npm run build
    ```
4.  **Run Migrations:**
    ```bash
    python -m cli db-migrate
    ```
5.  **Run Application:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

---

## 🔧 Database CLI Commands | أوامر CLI لقاعدة البيانات

All CLI commands are now run through the unified `cli.py` entrypoint.

### Create Tables | إنشاء الجداول
```bash
python -m cli db create-all
```

### Seed Database | ملء قاعدة البيانات
```bash
python -m cli db seed --confirm
```

### Run Migrations | تشغيل الترحيلات
```bash
python -m cli db-migrate
```
---

## 🛠️ Technology Stack | التقنيات المستخدمة

### Backend
- **FastAPI** - High-performance web framework
- **SQLAlchemy 2.0 / SQLModel** - ORM
- **Alembic** - Database migrations
- **PostgreSQL / Supabase** - Primary database
- **SQLite** - Development/Testing
- **Typer** - Modern CLI framework

### Frontend
- **React + TypeScript** - Modern UI
- **Vite** - Build tool

---
