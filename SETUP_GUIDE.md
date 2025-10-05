# 🚀 CogniForge Setup Guide - دليل الإعداد

## Overview / نظرة عامة

This guide will help you set up CogniForge for local development using Docker Compose.
هذا الدليل سيساعدك على إعداد CogniForge للتطوير المحلي باستخدام Docker Compose.

---

## ⚠️ Important: Database Configuration

**CogniForge supports TWO database modes:**

### 1. **Local Database (Recommended for Development)** ✅
- Uses Docker Compose with local PostgreSQL container
- Faster and works offline
- No external dependencies
- **This is the default configuration**

### 2. **Remote Supabase Database** 🌐
- Uses external Supabase PostgreSQL
- Requires internet connection
- For production or remote collaboration

---

## 🔧 Quick Setup (Local Database)

### Option A: Automated Setup (Recommended) 🚀

```bash
# Run the setup script
./setup-env.sh
```

This script will:
- Create `.env` from `.env.example`
- Configure for local database automatically
- Guide you through the setup process

### Option B: Manual Setup

If you prefer to set up manually, follow these steps:

### Step 1: Copy Environment File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` and ensure these lines are configured for **local database**:

```bash
# For LOCAL development with Docker Compose:
DATABASE_PASSWORD=Aog2Df4lIlIXiCGk
DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD}@db:5432/postgres
```

**Key Points:**
- The hostname is `db` (the Docker Compose service name)
- **NOT** `db.aocnuqhxrhxgbfcgbxfy.supabase.co` (remote Supabase)

### Step 3: Start Services

```bash
# Start database and application
docker-compose up -d
```

### Step 4: Run Migrations

```bash
# Apply database migrations
docker-compose run --rm web flask db upgrade

# Or create new migration
docker-compose run --rm web flask db migrate -m "Your migration message"
```

### Step 5: Create Admin User

```bash
docker-compose run --rm web flask users create-admin
```

---

## 🌐 Remote Supabase Configuration (Optional)

If you want to use **remote Supabase** instead:

### Step 1: Update .env

Replace the DATABASE_URL in `.env` with your Supabase connection string:

```bash
# For REMOTE Supabase:
DATABASE_URL=postgresql://postgres.your-project-id:your-password@aws-0-region.pooler.supabase.com:5432/postgres
```

### Step 2: Remove Local Database Dependency

You'll need to modify `docker-compose.yml` or ensure your services don't depend on the local `db` service.

---

## 🐛 Common Issues / المشاكل الشائعة

### Issue 1: "Cannot assign requested address" Error ⚠️

**This is the MOST COMMON issue when setting up CogniForge!**

**Error Message:**
```
psycopg2.OperationalError: connection to server at "db.aocnuqhxrhxgbfcgbxfy.supabase.co" (2a05:d012:42e:5712:e46:41a4:b061:a164), port 5432 failed: Cannot assign requested address
```

**What This Means:**
- You're trying to run `docker-compose run --rm web flask db migrate/upgrade`
- But your `.env` file has `DATABASE_URL` pointing to remote Supabase
- Docker Compose expects a local database (the `db` service)

**Root Cause:**
- Missing or incorrectly configured `.env` file
- The app is trying to connect to remote Supabase instead of local Docker database

**Solution:**
```bash
# Quick fix - run the setup script:
./setup-env.sh

# OR manually edit .env and change DATABASE_URL to:
DATABASE_URL=postgresql://postgres:Aog2Df4lIlIXiCGk@db:5432/postgres

# Then restart your services:
docker-compose down
docker-compose up -d

# Now try your migration again:
docker-compose run --rm web flask db upgrade
```

### Issue 2: ".env file not found"

**Cause:**
- You haven't created the `.env` file

**Solution:**
```bash
cp .env.example .env
# Then edit .env with your configuration
```

### Issue 3: "Database connection failed"

**Cause:**
- Database container is not running

**Solution:**
```bash
# Start the database
docker-compose up -d db

# Wait for it to be healthy
docker-compose ps

# Then try your command again
docker-compose run --rm web flask db upgrade
```

---

## ✅ Verify Your Setup

### Check Database Connection

```bash
# Inside the web container:
docker-compose run --rm web python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
"
```

**Expected output for LOCAL database:**
```
DATABASE_URL: postgresql://postgres:Aog2Df4lIlIXiCGk@db:5432/postgres
```

### Check Database is Running

```bash
docker-compose ps
```

**Expected output:**
```
NAME                IMAGE                        STATUS
cogniforge-db       supabase/postgres:15.1.0.118 Up (healthy)
```

---

## 📋 Environment Variables Reference

### Required Variables

```bash
# Flask Configuration
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

# Database (LOCAL)
DATABASE_PASSWORD=Aog2Df4lIlIXiCGk
DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD}@db:5432/postgres

# Admin User
ADMIN_EMAIL=benmerahhoussam16@gmail.com
ADMIN_PASSWORD=1111
ADMIN_NAME="Houssam Benmerah"

# AI Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
DEFAULT_AI_MODEL=openai/gpt-4o-mini
```

---

## 🎯 Next Steps

After successful setup:

1. **Access the application:**
   ```
   http://localhost:5000
   ```

2. **Access admin dashboard:**
   ```
   http://localhost:5000/admin/dashboard
   ```

3. **Database management:**
   ```
   http://localhost:5000/admin/database
   ```

4. **Run CLI commands:**
   ```bash
   docker-compose run --rm web flask db health
   docker-compose run --rm web flask db stats
   docker-compose run --rm web flask db tables
   ```

---

## 📚 Additional Documentation

- **Database Guide:** [`DATABASE_GUIDE_AR.md`](DATABASE_GUIDE_AR.md)
- **Database System:** [`DATABASE_SYSTEM_SUPREME_AR.md`](DATABASE_SYSTEM_SUPREME_AR.md)
- **Quick Reference:** [`DATABASE_QUICK_REFERENCE.md`](DATABASE_QUICK_REFERENCE.md)
- **Supabase Setup:** [`SUPABASE_COMPLETE_SETUP.md`](SUPABASE_COMPLETE_SETUP.md)

---

## 🆘 Getting Help

If you encounter issues:

1. Check this guide's "Common Issues" section
2. Review the error messages carefully
3. Verify your `.env` configuration
4. Check that Docker containers are running
5. Review logs: `docker-compose logs web`

---

**Built with ❤️ by Houssam Benmerah**
