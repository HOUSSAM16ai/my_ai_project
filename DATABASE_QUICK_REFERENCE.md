# 🚀 DATABASE SYSTEM QUICK REFERENCE | مرجع سريع لنظام قاعدة البيانات

## ⚡ Quick Commands | الأوامر السريعة

### Database Management CLI Commands
```bash
# Health Check (فحص الصحة)
flask database health

# Statistics (إحصائيات)
flask database stats

# List Tables (قائمة الجداول)
flask database tables

# Show Schema (عرض المخطط)
flask database schema <table_name>

# Optimize (تحسين)
flask database optimize

# Backup (نسخ احتياطي)
flask database backup
flask database backup --output=/path/to/backup
```

### Database Migration CLI Commands (Flask-Migrate)
```bash
# Create migration (إنشاء ترحيل)
flask db migrate -m "migration message"

# Apply migrations (تطبيق الترحيلات)
flask db upgrade

# Rollback migrations (التراجع عن الترحيلات)
flask db downgrade

# Show current version (عرض الإصدار الحالي)
flask db current

# Show migration history (عرض تاريخ الترحيلات)
flask db history
```

## 🌐 Web Interface

### Admin Dashboard
```
URL: http://localhost:5000/admin/database
Login: benmerahhoussam16@gmail.com
Password: 1111
```

### API Endpoints

#### Health & Stats
```bash
# Health Check
curl http://localhost:5000/admin/api/database/health

# Database Stats
curl http://localhost:5000/admin/api/database/stats

# All Tables
curl http://localhost:5000/admin/api/database/tables

# Table Schema
curl http://localhost:5000/admin/api/database/schema/users
```

#### Data Operations
```bash
# Get Table Data
curl "http://localhost:5000/admin/api/database/table/users?page=1&per_page=20"

# Search
curl "http://localhost:5000/admin/api/database/table/users?search=admin"

# Get Record
curl http://localhost:5000/admin/api/database/record/users/1

# Create Record (POST with JSON)
curl -X POST http://localhost:5000/admin/api/database/record/subjects \
  -H "Content-Type: application/json" \
  -d '{"name": "Math", "description": "Mathematics"}'

# Update Record (PUT with JSON)
curl -X PUT http://localhost:5000/admin/api/database/record/users/1 \
  -H "Content-Type: application/json" \
  -d '{"full_name": "New Name"}'

# Delete Record
curl -X DELETE http://localhost:5000/admin/api/database/record/users/1

# Export Table
curl http://localhost:5000/admin/api/database/export/users
```

#### Query Operations
```bash
# Execute SQL Query (POST)
curl -X POST http://localhost:5000/admin/api/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users LIMIT 10"}'
```

## 📊 Available Tables

### Core
- 👤 **users** - User accounts

### Education
- 📚 **subjects** - Academic subjects
- 📖 **lessons** - Lesson content  
- ✏️ **exercises** - Exercises
- 📝 **submissions** - Student submissions

### Overmind
- 🎯 **missions** - AI missions
- 📋 **mission_plans** - Mission plans
- ✅ **tasks** - Tasks
- 📊 **mission_events** - Event logs

### Admin
- 💬 **admin_conversations** - Conversations
- 💌 **admin_messages** - Messages

## 🔥 Common Tasks

### 1. Check Database Health
```bash
flask database health
```

### 2. View All Tables
```bash
flask database tables
```

### 3. Inspect Table Structure
```bash
flask database schema users
flask database schema missions
```

### 4. Optimize Database
```bash
flask database optimize
```

### 5. Create Backup
```bash
flask database backup
```

### 6. Apply Database Migrations
```bash
# Create a new migration
flask db migrate -m "Add new column"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

### 7. Search Records
```bash
# Via API
curl "http://localhost:5000/admin/api/database/table/missions?search=analyze"
```

## 🎯 Python Usage

```python
from app import create_app, db
from app.services import database_service

app = create_app()
with app.app_context():
    # Get all tables
    tables = database_service.get_all_tables()
    
    # Get table data
    data = database_service.get_table_data('users', page=1, per_page=20)
    
    # Health check
    health = database_service.get_database_health()
    
    # Get schema
    schema = database_service.get_table_schema('users')
    
    # Optimize
    result = database_service.optimize_database()
    
    # Export
    export = database_service.export_table_data('missions')
```

## 📈 Performance Tips

1. **Use caching**: Results cached for 5 minutes
2. **Optimize regularly**: `flask db optimize` weekly
3. **Monitor health**: `flask db health` daily
4. **Backup often**: `flask db backup` before major changes
5. **Index usage**: Check schema for proper indexes

## 🔒 Security

- ✅ Admin authentication required
- ✅ SQL injection protection
- ✅ Only SELECT queries allowed (custom SQL)
- ✅ Safe error handling
- ✅ Permission checks on all operations

## 🌟 Features

- ⚡ Fast response times (< 10ms)
- 📊 Real-time statistics
- 🔍 Advanced search & filtering
- 💾 Easy backup & restore
- 🏥 Health monitoring
- ⚙️ Auto-optimization
- 🎨 Beautiful CLI output
- 🌐 RESTful API
- 📱 Web interface

## 🎉 Quick Start

1. **Install**
```bash
pip install -r requirements.txt
flask db upgrade
```

2. **Create Admin**
```bash
flask users create-admin
```

3. **Access**
```
http://localhost:5000/admin/database
```

4. **Explore!**
- View tables
- Search & filter
- Export data
- Run queries

---

**Built with ❤️ for CogniForge**
