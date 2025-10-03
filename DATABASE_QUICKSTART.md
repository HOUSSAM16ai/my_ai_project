# 🗄️ Quick Start - Database Management

## Instant Access / الوصول السريع

```
URL: http://localhost:5000/admin/database
Login: benmerahhoussam16@gmail.com
Password: 1111
```

## What You Can Do / ما يمكنك فعله

✅ View ALL database tables  
✅ Search & filter data  
✅ Edit any record  
✅ Delete records  
✅ Add new records  
✅ Run custom SQL queries  
✅ Export to JSON  

## Supported Tables / الجداول

- users, subjects, lessons, exercises, submissions
- missions, mission_plans, tasks, mission_events
- admin_conversations, admin_messages

## Files / الملفات

- `app/services/database_service.py` - Backend service
- `app/admin/routes.py` - API endpoints
- `app/admin/templates/database_management.html` - UI
- `DATABASE_GUIDE_AR.md` - Full Arabic guide
- `DATABASE_MANAGEMENT.md` - Technical docs
- `IMPLEMENTATION_SUMMARY.md` - Complete summary

## Environment / البيئة

```bash
DATABASE_URL=postgresql://postgres:pass@host:5432/postgres
ADMIN_EMAIL=benmerahhoussam16@gmail.com
ADMIN_PASSWORD=1111
```

## Start Using / ابدأ الاستخدام

1. Login as admin
2. Click "Database" in navigation
3. Select a table
4. Start managing!

Built with ❤️ for CogniForge
