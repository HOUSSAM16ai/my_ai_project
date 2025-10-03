# Supabase Connection Verification

This directory contains a script to verify the connection to Supabase database (local or remote).

## Files

- `verify_supabase_connection.py` - Main verification script
- `SUPABASE_CONNECTION_SUCCESS_AR.md` - Success report in Arabic
- `QUICK_START_AR.md` - Quick start guide in Arabic

## Usage

### Quick Verification

```bash
python verify_supabase_connection.py
```

### What It Checks

The script performs the following checks:

1. ✅ **Environment Variables** - Verifies DATABASE_URL is configured
2. ✅ **Flask Application** - Tests app initialization
3. ✅ **Database Connection** - Connects to PostgreSQL/Supabase
4. ✅ **Database Info** - Shows PostgreSQL version and database name
5. ✅ **Tables List** - Lists all available tables
6. ✅ **Database Service** - Tests the database management service

### Expected Output

On success, you should see:

```
======================================================================
             🗄️ Supabase Database Connection Verification             
======================================================================

ℹ️  Step 1: Checking environment variables...
✅ DATABASE_URL found: postgresql://postgres:****@localhost:5432/postgres

ℹ️  Step 2: Importing Flask application...
✅ Flask app and database modules imported successfully

ℹ️  Step 3: Creating application context...
✅ Application created successfully

ℹ️  Step 4: Testing database connection...
✅ Database connection successful!
✅ PostgreSQL Version: PostgreSQL 15.1
✅ Connected to database: postgres

ℹ️  Step 5: Checking available tables...
✅ Found 13 tables in database:
  📋 users
  📋 subjects
  📋 lessons
  ...

ℹ️  Step 6: Testing database service...
✅ Database service working!
✅ Total records across all tables: 0

======================================================================
                 ✅ Connection Verification Complete!                  
======================================================================
```

## Prerequisites

1. **Docker** - For running the database container
2. **Python 3.8+** - For running the script
3. **Dependencies** - Install with:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### 1. Create .env file

```bash
cp .env.example .env
```

Edit `.env` and ensure these settings:

```bash
DATABASE_PASSWORD=Aog2Df4lIlIXiCGk
DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD}@db:5432/postgres
```

### 2. Start database

```bash
docker compose up -d db
```

Wait for it to be healthy (10-15 seconds).

### 3. Run migrations

```bash
DATABASE_URL="postgresql://postgres:Aog2Df4lIlIXiCGk@localhost:5432/postgres" flask db upgrade
```

### 4. Verify connection

```bash
python verify_supabase_connection.py
```

## Troubleshooting

### Error: "DATABASE_URL not found"

**Solution:** Create `.env` file from `.env.example` and set DATABASE_URL

### Error: "could not translate host name 'db'"

**Solution:** The script automatically handles this by replacing 'db' with 'localhost' when running outside Docker.

### Error: "No tables found"

**Solution:** Run database migrations:
```bash
DATABASE_URL="postgresql://postgres:Aog2Df4lIlIXiCGk@localhost:5432/postgres" flask db upgrade
```

### Error: Connection refused

**Solution:** Ensure database container is running:
```bash
docker compose up -d db
docker compose ps db  # Should show "healthy"
```

## Features

- 🎨 **Colored Output** - Easy to read terminal output with colors
- 🔍 **Comprehensive Checks** - Tests all aspects of database connectivity
- 🛡️ **Password Masking** - Hides sensitive data in output
- 🔄 **Docker Support** - Works both inside and outside Docker
- 📊 **Detailed Info** - Shows database version, tables, and statistics

## Exit Codes

- `0` - Success, all checks passed
- `1` - Failure, one or more checks failed

## Integration

This script can be used in:

- CI/CD pipelines for testing database connectivity
- Health checks before deployment
- Development environment setup verification
- Automated testing workflows

## Documentation

For more details, see:

- [SUPABASE_CONNECTION_SUCCESS_AR.md](SUPABASE_CONNECTION_SUCCESS_AR.md) - Success report (Arabic)
- [QUICK_START_AR.md](QUICK_START_AR.md) - Quick start guide (Arabic)
- [DATABASE_GUIDE_AR.md](DATABASE_GUIDE_AR.md) - Database management guide (Arabic)
- [DATABASE_MANAGEMENT.md](DATABASE_MANAGEMENT.md) - Technical documentation (English)

---

Built with ❤️ for CogniForge Project
