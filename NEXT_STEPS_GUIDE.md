# 🚀 Next Steps - Setup and Deployment Scripts

This document describes the essential scripts for setting up and running the CogniForge application.

## 📋 Overview | نظرة عامة

These three scripts provide a streamlined process to get your application up and running:

1. **`apply_migrations.py`** - Apply database migrations
2. **`setup_supabase_connection.py`** - Verify Supabase connection
3. **`run.py`** - Start the application

## 🔄 Step 1: Apply Migrations

**Purpose**: This script applies all pending database migrations to ensure your database schema is up to date.

### Usage:
```bash
python3 apply_migrations.py
```

### What it does:
- ✅ Checks database connectivity
- ✅ Displays current migration status
- ✅ Applies all pending migrations
- ✅ Verifies successful application
- ✅ Lists all database tables

### Example Output:
```
======================================================================
                    Apply Database Migrations                    
======================================================================

ℹ️  Step 1: Checking database connection...
✅ Database connection successful!

ℹ️  Step 2: Checking current migration status...
✅ Found 4 applied migration(s)
ℹ️  Current migration: c670e137ea84_add_admin_ai_chat_system

ℹ️  Step 3: Applying migrations...
✅ Migrations applied successfully!

✅ Migrations Applied Successfully
✅ Database schema is up to date!
```

### Troubleshooting:
- **Database connection failed**: Ensure your database is running and `DATABASE_URL` in `.env` is correct
- **Flask command not found**: Install dependencies with `pip install -r requirements.txt`
- **Migration timeout**: Some migrations take longer - this is normal for large schema changes

---

## 🔍 Step 2: Verify Supabase Connection

**Purpose**: This script verifies that your Supabase database connection is working correctly.

### Usage:
```bash
python3 setup_supabase_connection.py
```

### What it does:
- ✅ Checks environment variables
- ✅ Tests database connectivity
- ✅ Verifies PostgreSQL version
- ✅ Lists all database tables
- ✅ Tests database service

### Example Output:
```
======================================================================
                Setup Supabase Database Connection                
======================================================================

ℹ️  Step 1: Checking environment variables...
✅ DATABASE_URL found: postgresql://postgres:****@...

ℹ️  Step 2: Importing Flask application...
✅ Flask app and database modules imported successfully

ℹ️  Step 3: Creating application context...
✅ Application created successfully

ℹ️  Step 4: Testing database connection...
✅ Database connection successful!
✅ PostgreSQL Version: PostgreSQL 15.1
✅ Connected to database: postgres

ℹ️  Step 5: Checking available tables...
✅ Found 11 tables in database:
  📋 admin_conversations
  📋 admin_messages
  📋 exercises
  📋 lessons
  ...

✅ Connection Setup Complete!
✅ Supabase database is accessible and ready to use
```

### Troubleshooting:
- **DATABASE_URL not found**: Copy `.env.example` to `.env` and configure your Supabase credentials
- **Database connection failed**: 
  - For Docker: Run `docker-compose up -d db`
  - For Supabase: Check your credentials in `.env`
- **No tables found**: Run `python3 apply_migrations.py` first

---

## 🚀 Step 3: Start Application

**Purpose**: This script starts the Flask application server.

### Usage:
```bash
python3 run.py
```

### What it does:
- ✅ Loads environment configuration
- ✅ Creates Flask application instance
- ✅ Starts the development server

### Example Output:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Access Points:
- **Main Application**: http://localhost:5000
- **Admin Dashboard**: http://localhost:5000/admin/dashboard
- **Database Management**: http://localhost:5000/admin/database

### Troubleshooting:
- **Port already in use**: Change the port with `flask run --port=8000`
- **Module not found**: Install dependencies with `pip install -r requirements.txt`
- **Database errors**: Make sure you've run steps 1 and 2 first

---

## 📝 Complete Workflow | سير العمل الكامل

For a fresh installation, follow these steps in order:

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python3 apply_migrations.py

# 4. Verify connection
python3 setup_supabase_connection.py

# 5. Start application
python3 run.py
```

## 🌐 When Internet Available | عند توفر الإنترنت

When you have internet connectivity, ensure you complete all three steps:

```bash
# Step 1: Apply Migrations
python3 apply_migrations.py

# Step 2: Verify Connection
python3 setup_supabase_connection.py

# Step 3: Start Application
python3 run.py
```

All three scripts must succeed for a complete setup! ✅

---

## 📚 Related Documentation

- **Database Guide**: See `DATABASE_GUIDE_AR.md` for detailed database documentation
- **Quick Reference**: See `DATABASE_QUICK_REFERENCE.md` for CLI commands
- **Supabase Setup**: See `SUPABASE_VERIFICATION_GUIDE_AR.md` for Supabase-specific setup

---

## 🔧 Script Details

### Features Common to All Scripts:

- **Color-coded output**: Easy to read success/error messages
- **Detailed error messages**: Clear information when something goes wrong
- **Step-by-step execution**: Visual progress through each phase
- **Graceful error handling**: Proper cleanup and informative failures

### Exit Codes:
- `0` - Success
- `1` - Failure (check output for details)

---

Built with ❤️ for CogniForge
