# 🔄 CLI Commands Migration Guide | دليل ترحيل الأوامر

## 📢 Important Change | تغيير مهم

The custom database management CLI commands have been moved from the `db` group to the `database` group to avoid conflicts with Flask-Migrate's built-in database migration commands.

تم نقل أوامر إدارة قاعدة البيانات المخصصة من مجموعة `db` إلى مجموعة `database` لتجنب التعارض مع أوامر الترحيل المدمجة في Flask-Migrate.

## 🔀 Command Changes | تغييرات الأوامر

### Old Commands (No longer work) | الأوامر القديمة (لم تعد تعمل)
```bash
flask db health      ❌ No longer available
flask db stats       ❌ No longer available
flask db tables      ❌ No longer available
flask db schema      ❌ No longer available
flask db optimize    ❌ No longer available
flask db backup      ❌ No longer available
```

### New Commands (Use these instead) | الأوامر الجديدة (استخدم هذه بدلاً منها)
```bash
flask database health    ✅ Use this
flask database stats     ✅ Use this
flask database tables    ✅ Use this
flask database schema    ✅ Use this
flask database optimize  ✅ Use this
flask database backup    ✅ Use this
```

## 🎯 Flask-Migrate Commands | أوامر Flask-Migrate

The `flask db` group is now reserved for Flask-Migrate migration commands:

مجموعة `flask db` محجوزة الآن لأوامر الترحيل الخاصة بـ Flask-Migrate:

```bash
# Create a new migration | إنشاء ترحيل جديد
flask db migrate -m "Migration message"

# Apply migrations | تطبيق الترحيلات
flask db upgrade

# Rollback migrations | التراجع عن الترحيلات
flask db downgrade

# Show current migration version | عرض إصدار الترحيل الحالي
flask db current

# Show migration history | عرض تاريخ الترحيلات
flask db history

# Initialize migrations directory | تهيئة مجلد الترحيلات
flask db init
```

## 📝 Quick Reference | مرجع سريع

### Database Management | إدارة قاعدة البيانات
Use `flask database <command>` for database management operations:
```bash
flask database health     # Check database health
flask database stats      # Show database statistics
flask database tables     # List all tables
flask database schema users  # Show table schema
flask database optimize   # Optimize database
flask database backup     # Create backup
```

### Database Migrations | ترحيلات قاعدة البيانات
Use `flask db <command>` for database migrations:
```bash
flask db migrate -m "Add new column"  # Create migration
flask db upgrade                       # Apply migrations
flask db downgrade                     # Rollback migrations
flask db current                       # Show current version
flask db history                       # Show migration history
```

## 🔧 Why This Change? | لماذا هذا التغيير؟

**Problem | المشكلة:**
- Both Flask-Migrate and custom database commands were using the same `db` CLI group
- This caused Flask-Migrate commands to be hidden/overridden
- Users couldn't run `flask db migrate` or `flask db upgrade`

**Solution | الحل:**
- Custom database commands moved to `database` group
- Flask-Migrate commands now work properly under `db` group
- Both sets of commands are now accessible and functional

## 📚 Documentation Updates | تحديثات التوثيق

The following documentation files have been updated:
- `DATABASE_QUICK_REFERENCE.md`
- `DATABASE_GUIDE_AR.md`
- `app/cli/database_commands.py` header comments

## 🚀 Need Help? | تحتاج مساعدة؟

If you have any scripts or automation that use the old commands, update them to use the new `flask database` commands instead of `flask db`.

إذا كان لديك أي سكريبتات أو أتمتة تستخدم الأوامر القديمة، قم بتحديثها لاستخدام أوامر `flask database` الجديدة بدلاً من `flask db`.

---

**Version:** 1.0  
**Date:** 2025-10-05  
**Status:** Active ✅
