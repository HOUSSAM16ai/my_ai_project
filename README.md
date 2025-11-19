# 🌟 CogniForge - The Superior AI-Powered Educational Platform

> **نظام تعليمي ذكي خارق مدعوم بالذكاء الاصطناعي**

> **🔥 REALITY KERNEL V3 ARCHITECTURE** → The project is now powered by a framework-agnostic, hyper-modular, self-healing architecture.

---

## 🚀 Overview | نظرة عامة

CogniForge is an advanced, AI-powered educational platform built on a next-generation system where Reality Kernel v3 is the central execution spine. All APIs are built in a fully framework-agnostic, hyper-modular architecture.

---

## 🎯 Quick Start | البدء السريع

### 1️⃣ Installation | التثبيت

```bash
# Clone repository
git clone https://github.com/HOUSSAM16ai/my_ai_project.git
cd my_ai_project

# Setup environment (IMPORTANT!)
cp .env.example .env
# Edit .env and configure your Supabase connection:
# DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres

# Install dependencies
pip install -r requirements.txt

# Run migrations
python -m cli db-migrate

# Seed the database (optional)
python -m cli db seed --confirm
```

### 2️⃣ Run Application | تشغيل التطبيق

```bash
# Run with Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access the application
# Application: http://localhost:8000
# API Docs: http://localhost:8000/docs
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
