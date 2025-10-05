# 📊 مثال على مخرجات سكريبت عرض الجداول
# Database Tables Viewer - Example Output

## الاستخدام / Usage

```bash
python3 list_database_tables.py
```

## مثال على المخرجات / Example Output

```
================================================================================
              📊 عرض جداول قاعدة البيانات / Database Tables Viewer              
================================================================================

================================================================================
                     📊 جداول قاعدة البيانات
                      📊 Database Tables
================================================================================

🔍 جاري الاتصال بقاعدة البيانات...
🔍 Connecting to database...

✅ الاتصال ناجح!
✅ Connection successful!

────────────────────────────────────────────────────────────────────────────────
📈 الإحصائيات العامة / General Statistics
────────────────────────────────────────────────────────────────────────────────
إجمالي عدد الجداول / Total Tables: 12
  • الجداول الأساسية / Core Tables: 5
  • جداول Overmind / Overmind Tables: 4
  • جداول الأدمن / Admin Tables: 2
  • جداول النظام / System Tables: 1

────────────────────────────────────────────────────────────────────────────────
📚 الجداول الأساسية / Core Tables (5)
────────────────────────────────────────────────────────────────────────────────
✅ 👤 users                      
   📝 الوصف / Description: جدول المستخدمين / User accounts
   🔢 عدد السجلات / Records: 15
   📋 عدد الأعمدة / Columns: 7

✅ 📚 subjects                   
   📝 الوصف / Description: جدول المواد الدراسية / Educational subjects
   🔢 عدد السجلات / Records: 8
   📋 عدد الأعمدة / Columns: 5

✅ 📖 lessons                    
   📝 الوصف / Description: جدول الدروس / Lessons
   🔢 عدد السجلات / Records: 42
   📋 عدد الأعمدة / Columns: 6

✅ ✏️  exercises                  
   📝 الوصف / Description: جدول التمارين / Exercises
   🔢 عدد السجلات / Records: 127
   📋 عدد الأعمدة / Columns: 8

✅ 📝 submissions                
   📝 الوصف / Description: جدول الإجابات / Student submissions
   🔢 عدد السجلات / Records: 534
   📋 عدد الأعمدة / Columns: 7

────────────────────────────────────────────────────────────────────────────────
🎯 جداول Overmind / Overmind Tables (4)
────────────────────────────────────────────────────────────────────────────────
✅ 🎯 missions                   
   📝 الوصف / Description: جدول المهام الرئيسية / Main missions
   🔢 عدد السجلات / Records: 23
   📋 عدد الأعمدة / Columns: 12

✅ 📋 mission_plans              
   📝 الوصف / Description: جدول خطط المهام / Mission plans
   🔢 عدد السجلات / Records: 45
   📋 عدد الأعمدة / Columns: 10

✅ ✅ tasks                       
   📝 الوصف / Description: جدول المهام الفرعية / Sub-tasks
   🔢 عدد السجلات / Records: 189
   📋 عدد الأعمدة / Columns: 15

✅ 📊 mission_events             
   📝 الوصف / Description: جدول أحداث المهام / Mission events
   🔢 عدد السجلات / Records: 412
   📋 عدد الأعمدة / Columns: 6

────────────────────────────────────────────────────────────────────────────────
💬 جداول الأدمن / Admin Tables (2)
────────────────────────────────────────────────────────────────────────────────
✅ 💬 admin_conversations        
   📝 الوصف / Description: جدول محادثات الأدمن / Admin conversations
   🔢 عدد السجلات / Records: 8
   📋 عدد الأعمدة / Columns: 5

✅ 💌 admin_messages             
   📝 الوصف / Description: جدول رسائل الأدمن / Admin messages
   🔢 عدد السجلات / Records: 67
   📋 عدد الأعمدة / Columns: 6

────────────────────────────────────────────────────────────────────────────────
🔧 جداول النظام / System Tables (1)
────────────────────────────────────────────────────────────────────────────────
✅ 🔄 alembic_version            
   📝 الوصف / Description: جدول إصدارات الهجرات / Migration versions
   📋 عدد الأعمدة / Columns: 1

────────────────────────────────────────────────────────────────────────────────
✅ التحقق من الجداول / Table Verification
────────────────────────────────────────────────────────────────────────────────
✅ جميع الجداول المتوقعة موجودة!
✅ All expected tables are present!

================================================================================
                              ✨ ملخص
                            ✨ Summary
================================================================================

📊 إجمالي الجداول / Total Tables: 12
✅ الجداول الموجودة / Present Tables: 12/12

✅ تم بنجاح! / Completed successfully!
```

## في حالة وجود جداول مفقودة / If Tables are Missing

```
────────────────────────────────────────────────────────────────────────────────
⚠️ جداول مفقودة / Missing Tables
────────────────────────────────────────────────────────────────────────────────
الجداول التالية متوقعة لكنها غير موجودة:
The following tables are expected but not found:

❌ 📚 subjects                    (جدول المواد الدراسية / Educational subjects)
❌ 📖 lessons                     (جدول الدروس / Lessons)
❌ 💬 admin_conversations         (جدول محادثات الأدمن / Admin conversations)
❌ 💌 admin_messages              (جدول رسائل الأدمن / Admin messages)

💡 لإنشاء الجداول المفقودة، قم بتشغيل:
💡 To create missing tables, run:
   flask db upgrade
```

## الميزات / Features

### 1. عرض منظم للجداول / Organized Table Display
- تصنيف الجداول حسب الفئة (أساسية، Overmind، إدارية)
- عرض أيقونات واضحة لكل جدول
- وصف بالعربية والإنجليزية

### 2. الإحصائيات التفصيلية / Detailed Statistics
- عدد السجلات في كل جدول
- عدد الأعمدة في كل جدول
- إحصائيات عامة عن قاعدة البيانات

### 3. التحقق من الجداول / Table Verification
- يتحقق من وجود جميع الجداول المتوقعة
- يعرض الجداول المفقودة
- يقدم توصيات للإصلاح

### 4. دعم لغتين / Bilingual Support
- جميع الرسائل بالعربية والإنجليزية
- سهل الاستخدام للناطقين بالعربية

### 5. ألوان واضحة / Clear Colors
- 🟢 أخضر للنجاح
- 🔴 أحمر للأخطاء
- 🟡 أصفر للتحذيرات
- 🔵 أزرق للمعلومات

## الأوامر المساعدة / Helper Commands

```bash
# عرض جميع الجداول
python3 list_database_tables.py

# التحقق من حالة الهجرات
python3 check_migrations_status.py

# تطبيق الهجرات المفقودة
flask db upgrade

# عرض معلومات عن نظام إدارة قاعدة البيانات
python3 demo_database_management.py
```

## متطلبات التشغيل / Requirements

1. ملف `.env` يحتوي على `DATABASE_URL`
2. تثبيت المكتبات المطلوبة:
   ```bash
   pip install flask sqlalchemy python-dotenv psycopg2-binary flask-sqlalchemy
   ```

## استكشاف الأخطاء / Troubleshooting

### خطأ: No module named 'dotenv'
```bash
pip install python-dotenv
```

### خطأ: Could not connect to database
- تحقق من ملف `.env`
- تأكد من صحة `DATABASE_URL`
- تحقق من تشغيل خادم قاعدة البيانات

### خطأ: Table does not exist
```bash
# تطبيق الهجرات
flask db upgrade
```

---

**الإصدار**: 1.0.0  
**التاريخ**: 2024  
**المؤلف**: CogniForge System
