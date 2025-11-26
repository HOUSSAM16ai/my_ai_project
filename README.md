# 🌟 CogniForge - The Superior AI-Powered Educational Platform

> **نظام تعليمي ذكي خارق مدعوم بالذكاء الاصطناعي**

> **🔥 REALITY KERNEL V3 ARCHITECTURE** → The project is now powered by a framework-agnostic, hyper-modular, self-healing architecture.

---

## 🚀 Overview | نظرة عامة

CogniForge is an advanced, AI-powered educational platform built on a next-generation system where Reality Kernel v3 is the central execution spine. All APIs are built in a fully framework-agnostic, hyper-modular architecture.

---

## 🎯 Quick Start | البدء السريع

### 1️⃣ Automated Setup & Run | الإعداد والتشغيل الآلي

To get started, simply run the development setup script. This will handle everything: installing dependencies, creating the `.env` file, building the frontend, and starting the server.

```bash
# Make the script executable (only needs to be done once)
chmod +x scripts/setup_dev.sh

# Run the setup script
./scripts/setup_dev.sh
```

The application will be available at `http://localhost:8000`.

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
