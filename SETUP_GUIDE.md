# 🚀 CogniForge Setup Guide - دليل الإعداد

## Overview / نظرة عامة

This guide will help you set up CogniForge using Supabase as the database.
هذا الدليل سيساعدك على إعداد CogniForge باستخدام Supabase كقاعدة بيانات.

---

## ⚠️ Important: Database Configuration

**CogniForge uses Supabase PostgreSQL database:**

### **Remote Supabase Database** 🌐
- Uses external Supabase PostgreSQL
- Requires internet connection
- Scalable and managed database solution
- **This is the only supported configuration**

---

## 🔧 Quick Setup (Supabase Database)

### Option A: Automated Setup (Recommended) 🚀

```bash
# Run the setup script
./setup-env.sh
```

This script will:
- Create `.env` from `.env.example`
- Guide you through the Supabase configuration
- Set up your database connection

### Option B: Manual Setup

If you prefer to set up manually, follow these steps:

### Step 1: Copy Environment File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` and configure your **Supabase database connection**:

```bash
# For Supabase (Remote Database):
DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres
```

**How to get your Supabase connection string:**
1. Go to your Supabase project dashboard
2. Navigate to Settings → Database
3. Find "Connection String" section
4. Copy the "URI" connection string
5. Replace `[YOUR-PASSWORD]` with your actual database password

**Key Points:**
- The hostname will be something like `aws-0-us-east-1.pooler.supabase.com`
- Make sure to use the pooler connection (port 5432)
- Replace the password placeholder with your actual password

### Step 3: Start Services

```bash
# Start application services (no local database needed)
docker-compose up -d
```

### Step 4: Run Migrations

```bash
# Apply database migrations to Supabase
docker-compose run --rm web flask db upgrade

# Or create new migration
docker-compose run --rm web flask db migrate -m "Your migration message"
```

### Step 5: Create Admin User

```bash
docker-compose run --rm web flask users create-admin
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

**Expected output for Supabase database:**
```
DATABASE_URL: postgresql://postgres.xxx:xxx@aws-0-xx.pooler.supabase.com:5432/postgres
```

### Check Services are Running

```bash
docker-compose ps
```

**Expected output:**
```
NAME                IMAGE                        STATUS
flask-frontend      my_ai_project-web           Up
fastapi-ai-service  my_ai_project-ai_service    Up
```

---

## 🐛 Common Issues / المشاكل الشائعة

### Issue 1: "Connection refused" or "Cannot connect to database" ⚠️

**Error Message:**
```
psycopg2.OperationalError: connection to server failed
```

**What This Means:**
- Your Supabase connection string is incorrect
- Or your Supabase database is not accessible

**Solution:**
```bash
# Verify your DATABASE_URL in .env:
# 1. Check the connection string format
# 2. Ensure the password is correct
# 3. Verify the hostname and port

# Test the connection:
docker-compose run --rm web python3 -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    print('Connection successful!')
"
```

### Issue 2: ".env file not found"

**Cause:**
- You haven't created the `.env` file

**Solution:**
```bash
cp .env.example .env
# Then edit .env with your Supabase configuration
```

### Issue 3: "Migration failed"

**Cause:**
- Database migrations haven't been applied to Supabase

**Solution:**
```bash
# Apply migrations to Supabase
docker-compose run --rm web flask db upgrade

# If that fails, check your connection first
docker-compose run --rm web python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
"
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
