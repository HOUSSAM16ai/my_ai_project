# 🔄 Migration to Supabase-Only Database

## Overview | نظرة عامة

This document explains the migration from local PostgreSQL to Supabase-only database configuration.

تشرح هذه الوثيقة الانتقال من قاعدة البيانات المحلية PostgreSQL إلى تكوين Supabase فقط.

---

## ✅ What Changed | ما الذي تغير

### 1. **Removed Local Database Container**
- ❌ Removed `db` service from `docker-compose.yml`
- ❌ Removed `pgdata` volume 
- ❌ Removed `depends_on` constraint from web service
- ✅ Now uses Supabase remote database exclusively

### 2. **Updated Configuration Files**
- **docker-compose.yml**: Removed local database service and volume
- **.devcontainer/devcontainer.json**: 
  - Removed port 5432 forwarding
  - Removed DB_HOST and DB_PORT environment variables
  - Set SKIP_DB_WAIT=true (no local database to wait for)
- **.env.example**: Updated with Supabase connection string template
- **SETUP_GUIDE.md**: Complete rewrite for Supabase-only setup
- **README.md**: Updated quick start instructions

---

## 🚀 How to Migrate | كيفية الانتقال

### Step 1: Get Your Supabase Connection String

1. Go to your Supabase project dashboard
2. Navigate to **Settings → Database**
3. Find the **Connection String** section
4. Copy the **URI** format (pooler connection recommended, port 6543)
5. It should look like:
   ```
   postgresql://postgres.xxxxx:your-password@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
   ```

### Step 2: Update Your .env File

Replace the old local database configuration:

```bash
# OLD (Local Database - NO LONGER SUPPORTED):
# DATABASE_PASSWORD=Aog2Df4lIlIXiCGk
# DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD}@db:5432/postgres
```

With your Supabase connection string:

```bash
# NEW (Supabase Remote Database - Pooler Recommended):
DATABASE_URL=postgresql://postgres.xxxxx:your-password@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```

### Step 3: Stop and Remove Old Containers

```bash
# Stop all services
docker-compose down

# Remove the old database volume (if you want to free up space)
docker volume rm my_ai_project_pgdata 2>/dev/null || true
```

### Step 4: Pull Latest Changes and Restart

```bash
# Pull the latest code
git pull

# Start the services (no local database needed!)
docker-compose up -d

# Run migrations to Supabase
docker-compose run --rm web flask db upgrade
```

---

## 💡 Benefits | الفوائد

### 1. **Resource Efficiency | كفاءة الموارد**
- ✅ No local PostgreSQL container consuming CPU/RAM
- ✅ No local storage used for database files
- ✅ Faster container startup (no database health checks)

### 2. **Scalability | قابلية التوسع**
- ✅ Managed database with automatic backups
- ✅ Better performance for production workloads
- ✅ Built-in connection pooling

### 3. **Simplicity | البساطة**
- ✅ One less service to manage
- ✅ Consistent database across all environments
- ✅ No local/remote database confusion

---

## 🔧 Troubleshooting | استكشاف الأخطاء

### Issue: "Cannot connect to database"

**Solution:**
1. Verify your DATABASE_URL is correct in `.env`
2. Check your Supabase password is not URL-encoded (or use percent-encoding: @ → %40, # → %23)
3. Ensure your IP is whitelisted in Supabase (if using direct connection)
4. Use the pooler connection (port 6543) for better performance, or direct connection (port 5432) for write-heavy operations

### Issue: "Old database data is lost"

**Don't worry!** Your local database data is still in the Docker volume `my_ai_project_pgdata`. 

To export it before deletion:
```bash
# Start only the old database temporarily
docker run -d --name temp-db \
  -v my_ai_project_pgdata:/var/lib/postgresql/data \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD=Aog2Df4lIlIXiCGk \
  supabase/postgres:15.1.0.118

# Export the data
docker exec temp-db pg_dump -U postgres postgres > backup.sql

# Stop and remove the temporary container
docker stop temp-db && docker rm temp-db
```

### Issue: "Migrations are out of sync"

**Solution:**
```bash
# Check current migration state
docker-compose run --rm web flask db current

# If needed, stamp the current version
docker-compose run --rm web flask db stamp head

# Then apply any new migrations
docker-compose run --rm web flask db upgrade
```

---

## 📝 Notes for Developers | ملاحظات للمطورين

### Development Workflow

1. **No more local database setup needed!** Just configure your `.env` with Supabase connection
2. **Migrations** are applied directly to Supabase
3. **All developers** can share the same development database or have separate Supabase projects
4. **Testing** still uses SQLite in-memory database (see `config.py`)

### Environment Variables

Only these database-related variables are needed now:
```bash
DATABASE_URL=postgresql://postgres.xxxxx:password@host:5432/postgres
```

You no longer need:
- ❌ `DATABASE_PASSWORD`
- ❌ `DB_HOST`
- ❌ `DB_PORT`
- ❌ `POSTGRES_USER`
- ❌ `POSTGRES_DB`

---

## ✅ Verification Checklist

After migration, verify:

- [ ] Services start successfully: `docker-compose up -d`
- [ ] Web service is running: `docker-compose ps`
- [ ] Database connection works: `docker-compose run --rm web flask db current`
- [ ] Application is accessible: `http://localhost:5000`
- [ ] Admin panel works: `http://localhost:5000/admin/dashboard`

---

## 🆘 Need Help? | تحتاج مساعدة؟

If you encounter issues:

1. Check the [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
2. Verify your `.env` configuration
3. Review the [Common Issues](SETUP_GUIDE.md#-common-issues--المشاكل-الشائعة) section
4. Open an issue on GitHub with:
   - Your `.env` configuration (without sensitive data)
   - Docker logs: `docker-compose logs web`
   - Error messages

---

**Last Updated:** 2025-01-06
**Migration Version:** v6.0
