# Database Management System Documentation

## نظام إدارة قاعدة البيانات - CogniForge

### Overview
تم إضافة نظام شامل لإدارة قاعدة البيانات من صفحة الأدمن. يتيح لك هذا النظام التحكم الكامل في جميع جداول قاعدة البيانات الموجودة في Supabase.

### Features / المميزات

#### 1. عرض شامل للجداول (Table Overview)
- قائمة بجميع الجداول في قاعدة البيانات
- عدد السجلات في كل جدول
- إحصائيات شاملة للقاعدة

#### 2. إدارة البيانات (Data Management)
- **عرض البيانات**: استعراض جميع السجلات في أي جدول مع ترقيم الصفحات
- **تعديل السجلات**: تحديث أي سجل مباشرة من الواجهة
- **حذف السجلات**: حذف السجلات غير المرغوب فيها
- **إضافة سجلات**: إنشاء سجلات جديدة

#### 3. استعلامات مخصصة (Custom Queries)
- تنفيذ استعلامات SQL مخصصة
- عرض النتائج في جدول منسق
- دعم استعلامات SELECT فقط للأمان

#### 4. تصدير البيانات (Data Export)
- تصدير أي جدول بصيغة JSON
- تنزيل البيانات مباشرة

### Tables Managed / الجداول المدارة

1. **users** - المستخدمين
   - الحسابات والصلاحيات
   - معلومات المستخدمين

2. **subjects** - المواد الدراسية
   - المواد التعليمية

3. **lessons** - الدروس
   - محتوى الدروس

4. **exercises** - التمارين
   - الأسئلة والتمارين

5. **submissions** - الإجابات المقدمة
   - إجابات الطلاب

6. **missions** - المهام
   - مهام Overmind

7. **mission_plans** - خطط المهام
   - التخطيط والاستراتيجيات

8. **tasks** - المهام الفرعية
   - المهام الفردية

9. **mission_events** - أحداث المهام
   - سجل الأحداث

10. **admin_conversations** - محادثات الأدمن
    - المحادثات مع الذكاء الاصطناعي

11. **admin_messages** - رسائل المحادثات
    - الرسائل الفردية

### API Endpoints

#### Get All Tables
```
GET /admin/api/database/tables
```

#### Get Database Stats
```
GET /admin/api/database/stats
```

#### Get Table Data
```
GET /admin/api/database/table/<table_name>?page=1&per_page=50
```

#### Get Single Record
```
GET /admin/api/database/record/<table_name>/<record_id>
```

#### Create Record
```
POST /admin/api/database/record/<table_name>
Content-Type: application/json

{
  "field1": "value1",
  "field2": "value2"
}
```

#### Update Record
```
PUT /admin/api/database/record/<table_name>/<record_id>
Content-Type: application/json

{
  "field1": "new_value1"
}
```

#### Delete Record
```
DELETE /admin/api/database/record/<table_name>/<record_id>
```

#### Execute Query
```
POST /admin/api/database/query
Content-Type: application/json

{
  "sql": "SELECT * FROM users WHERE is_admin = true"
}
```

#### Export Table
```
GET /admin/api/database/export/<table_name>
```

### Usage / الاستخدام

#### 1. الوصول إلى صفحة إدارة قاعدة البيانات
```
URL: /admin/database
```
يجب أن تكون مسجل دخول كمسؤول (is_admin = true)

#### 2. اختيار جدول
- انقر على اسم الجدول من القائمة الجانبية
- سيتم عرض جميع السجلات

#### 3. تعديل سجل
- انقر على زر التعديل (✏️) بجوار السجل
- قم بتعديل الحقول
- انقر على "Save"

#### 4. حذف سجل
- انقر على زر الحذف (🗑️)
- أكد الحذف

#### 5. تنفيذ استعلام مخصص
- انقر على "Custom Query"
- اكتب استعلام SQL
- انقر على "Execute Query"

#### 6. تصدير بيانات
- اختر الجدول
- انقر على "Export"
- سيتم تنزيل ملف JSON

### Security / الأمان

1. **مصادقة المسؤول**: جميع النقاط تتطلب تسجيل دخول كمسؤول
2. **استعلامات آمنة**: يتم قبول استعلامات SELECT فقط
3. **معالجة الأخطاء**: معالجة شاملة للأخطاء مع رسائل واضحة

### Environment Variables Required

تأكد من وجود المتغيرات التالية في ملف .env:

```bash
# Database Configuration
DATABASE_PASSWORD=your_database_password
DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD}@db:5432/postgres

# Or for Supabase:
DATABASE_URL=postgresql://postgres.your-project:password@aws-0-region.pooler.supabase.com:5432/postgres

# Admin User
ADMIN_EMAIL=benmerahhoussam16@gmail.com
ADMIN_PASSWORD=1111
ADMIN_NAME="Houssam Benmerah"
```

### Screenshots

لعرض واجهة إدارة قاعدة البيانات، قم بزيارة:
```
http://localhost:5000/admin/database
```

### File Structure

```
app/
├── services/
│   └── database_service.py      # خدمة إدارة قاعدة البيانات
├── admin/
│   ├── routes.py                # نقاط نهاية API
│   └── templates/
│       └── database_management.html  # واجهة المستخدم
```

### Future Enhancements / التحسينات المستقبلية

1. ✅ البحث والتصفية في البيانات
2. ✅ فرز الأعمدة
3. ✅ تصدير بصيغ متعددة (CSV, Excel)
4. ✅ استيراد البيانات
5. ✅ نسخ احتياطي واستعادة
6. ✅ سجل التغييرات (Audit Log)
7. ✅ إدارة العلاقات بين الجداول
8. ✅ محرر متقدم للحقول JSON

### Support

للمساعدة أو الإبلاغ عن مشاكل:
- افتح Issue على GitHub
- راسل المطور

### License

هذا المشروع جزء من CogniForge ويخضع لنفس الترخيص.
