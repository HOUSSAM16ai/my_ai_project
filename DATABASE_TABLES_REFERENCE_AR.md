# 📊 مرجع سريع للجداول - Database Tables Quick Reference

## نظرة عامة / Overview
هذا المستند يحتوي على قائمة كاملة بجميع الجداول في قاعدة البيانات مع شرح مختصر لكل جدول.

---

## 📚 الجداول الأساسية (Core Tables)

### 1. 👤 users - جدول المستخدمين
**الوظيفة**: تخزين معلومات حسابات المستخدمين والصلاحيات

**الأعمدة الرئيسية**:
- `id` - معرف المستخدم (Primary Key)
- `full_name` - الاسم الكامل
- `email` - البريد الإلكتروني (فريد)
- `password_hash` - كلمة المرور المشفرة
- `is_admin` - هل المستخدم مسؤول؟
- `created_at` - تاريخ الإنشاء
- `updated_at` - تاريخ آخر تحديث

**الاستخدام**: إدارة المستخدمين، تسجيل الدخول، الصلاحيات

---

### 2. 📚 subjects - جدول المواد الدراسية
**الوظيفة**: تخزين المواد والمقررات التعليمية

**الأعمدة الرئيسية**:
- `id` - معرف المادة
- `name` - اسم المادة
- `description` - وصف المادة
- `created_at` - تاريخ الإنشاء

**الاستخدام**: تنظيم المحتوى التعليمي، تصنيف الدروس

---

### 3. 📖 lessons - جدول الدروس
**الوظيفة**: تخزين الدروس والمحتوى التعليمي

**الأعمدة الرئيسية**:
- `id` - معرف الدرس
- `subject_id` - معرف المادة (Foreign Key)
- `title` - عنوان الدرس
- `content` - محتوى الدرس
- `order` - ترتيب الدرس
- `created_at` - تاريخ الإنشاء

**الاستخدام**: إدارة الدروس، عرض المحتوى التعليمي

---

### 4. ✏️ exercises - جدول التمارين
**الوظيفة**: تخزين التمارين والأسئلة

**الأعمدة الرئيسية**:
- `id` - معرف التمرين
- `lesson_id` - معرف الدرس (Foreign Key)
- `question` - نص السؤال
- `answer` - الإجابة الصحيحة
- `type` - نوع السؤال
- `difficulty` - مستوى الصعوبة
- `created_at` - تاريخ الإنشاء

**الاستخدام**: إدارة الأسئلة، التقييم، الاختبارات

---

### 5. 📝 submissions - جدول الإجابات
**الوظيفة**: تخزين إجابات وتقديمات الطلاب

**الأعمدة الرئيسية**:
- `id` - معرف الإجابة
- `user_id` - معرف الطالب (Foreign Key)
- `exercise_id` - معرف التمرين (Foreign Key)
- `answer` - إجابة الطالب
- `score` - النتيجة
- `submitted_at` - تاريخ التقديم

**الاستخدام**: تتبع إجابات الطلاب، التقييم، الإحصائيات

---

## 🎯 جداول Overmind (AI System Tables)

### 6. 🎯 missions - جدول المهام الرئيسية
**الوظيفة**: تخزين المهام والأهداف الرئيسية للذكاء الاصطناعي

**الأعمدة الرئيسية**:
- `id` - معرف المهمة
- `objective` - هدف المهمة
- `status` - حالة المهمة (PENDING, RUNNING, SUCCESS, FAILED, etc.)
- `initiator_id` - معرف المستخدم الذي أنشأ المهمة (Foreign Key)
- `active_plan_id` - معرف الخطة النشطة (Foreign Key)
- `result_summary` - ملخص النتيجة
- `locked` - هل المهمة مقفلة؟
- `total_cost_usd` - التكلفة الإجمالية
- `adaptive_cycles` - عدد دورات التكيف
- `created_at` - تاريخ الإنشاء

**الاستخدام**: إدارة مهام الذكاء الاصطناعي، تتبع التقدم

---

### 7. 📋 mission_plans - جدول خطط المهام
**الوظيفة**: تخزين خطط تنفيذ المهام المختلفة

**الأعمدة الرئيسية**:
- `id` - معرف الخطة
- `mission_id` - معرف المهمة (Foreign Key)
- `version` - رقم إصدار الخطة
- `planner_name` - اسم المخطط (AI Model)
- `status` - حالة الخطة (DRAFT, VALID, SUPERSEDED, FAILED)
- `score` - تقييم الخطة
- `rationale` - التبرير
- `raw_json` - البيانات الخام (JSON)
- `stats_json` - الإحصائيات (JSON)
- `content_hash` - تجزئة المحتوى

**الاستخدام**: إدارة خطط المهام، المقارنة بين الخطط

---

### 8. ✅ tasks - جدول المهام الفرعية
**الوظيفة**: تخزين المهام الفرعية والخطوات التفصيلية

**الأعمدة الرئيسية**:
- `id` - معرف المهمة الفرعية
- `mission_id` - معرف المهمة الرئيسية (Foreign Key)
- `plan_id` - معرف الخطة (Foreign Key)
- `task_key` - مفتاح المهمة
- `description` - وصف المهمة
- `task_type` - نوع المهمة (TOOL, SYSTEM, META, VERIFICATION)
- `tool_name` - اسم الأداة
- `tool_args_json` - معاملات الأداة (JSON)
- `status` - حالة المهمة (PENDING, RUNNING, SUCCESS, FAILED, RETRY, SKIPPED)
- `priority` - الأولوية
- `risk_level` - مستوى المخاطرة
- `attempt_count` - عدد المحاولات
- `result_text` - نص النتيجة
- `result_meta_json` - معلومات إضافية عن النتيجة (JSON)
- `started_at` - وقت البدء
- `finished_at` - وقت الانتهاء
- `duration_ms` - المدة بالميلي ثانية

**الاستخدام**: تنفيذ المهام، تتبع التقدم التفصيلي

---

### 9. 📊 mission_events - جدول أحداث المهام
**الوظيفة**: تخزين سجل الأحداث والتغييرات في المهام

**الأعمدة الرئيسية**:
- `id` - معرف الحدث
- `mission_id` - معرف المهمة (Foreign Key)
- `task_id` - معرف المهمة الفرعية (Foreign Key، اختياري)
- `event_type` - نوع الحدث (CREATED, STATUS_CHANGE, TASK_COMPLETED, etc.)
- `payload` - بيانات الحدث (JSON)
- `note` - ملاحظة
- `created_at` - تاريخ الحدث

**الاستخدام**: تتبع تاريخ المهمة، التحليل، المراقبة

---

## 💬 جداول الأدمن (Admin Tables)

### 10. 💬 admin_conversations - جدول محادثات الأدمن
**الوظيفة**: تخزين محادثات الذكاء الاصطناعي مع الإدارة

**الأعمدة الرئيسية**:
- `id` - معرف المحادثة
- `user_id` - معرف المستخدم (Foreign Key)
- `title` - عنوان المحادثة
- `status` - حالة المحادثة
- `created_at` - تاريخ الإنشاء
- `updated_at` - تاريخ آخر تحديث

**الاستخدام**: إدارة المحادثات مع الذكاء الاصطناعي

---

### 11. 💌 admin_messages - جدول رسائل الأدمن
**الوظيفة**: تخزين رسائل المحادثات التفصيلية

**الأعمدة الرئيسية**:
- `id` - معرف الرسالة
- `conversation_id` - معرف المحادثة (Foreign Key)
- `role` - دور المرسل (user, assistant, system, tool)
- `content` - محتوى الرسالة
- `metadata` - معلومات إضافية (JSON)
- `created_at` - تاريخ الإرسال

**الاستخدام**: تخزين سجل المحادثات، السياق

---

## 🔧 جداول النظام (System Tables)

### 12. 🔄 alembic_version - جدول إصدارات الهجرات
**الوظيفة**: تتبع إصدارات هجرات قاعدة البيانات

**الأعمدة الرئيسية**:
- `version_num` - رقم إصدار الهجرة (Primary Key)

**الاستخدام**: إدارة الهجرات، التحكم في الإصدارات

---

## 🔗 العلاقات بين الجداول (Table Relationships)

### علاقات المستخدمين:
- `users` → `missions` (مستخدم واحد → مهام متعددة)
- `users` → `submissions` (مستخدم واحد → إجابات متعددة)
- `users` → `admin_conversations` (مستخدم واحد → محادثات متعددة)

### علاقات المحتوى التعليمي:
- `subjects` → `lessons` (مادة واحدة → دروس متعددة)
- `lessons` → `exercises` (درس واحد → تمارين متعددة)
- `exercises` → `submissions` (تمرين واحد → إجابات متعددة)

### علاقات Overmind:
- `missions` → `mission_plans` (مهمة واحدة → خطط متعددة)
- `missions` → `tasks` (مهمة واحدة → مهام فرعية متعددة)
- `missions` → `mission_events` (مهمة واحدة → أحداث متعددة)
- `mission_plans` → `tasks` (خطة واحدة → مهام متعددة)
- `tasks` → `mission_events` (مهمة فرعية واحدة → أحداث متعددة)
- `tasks` → `tasks` (مهمة تعتمد على مهام أخرى - task_dependencies)

### علاقات الأدمن:
- `admin_conversations` → `admin_messages` (محادثة واحدة → رسائل متعددة)

---

## 📈 الإحصائيات النموذجية (Typical Statistics)

| الجدول / Table | الفئة / Category | السجلات المتوقعة / Expected Records |
|----------------|------------------|-------------------------------------|
| users | Core | 10-1000 |
| subjects | Core | 5-50 |
| lessons | Core | 20-500 |
| exercises | Core | 100-10000 |
| submissions | Core | 500-100000 |
| missions | Overmind | 10-1000 |
| mission_plans | Overmind | 20-2000 |
| tasks | Overmind | 100-10000 |
| mission_events | Overmind | 200-50000 |
| admin_conversations | Admin | 5-100 |
| admin_messages | Admin | 50-1000 |
| alembic_version | System | 1-20 |

---

## 🎯 الاستخدامات الشائعة (Common Use Cases)

### 1. تتبع تقدم الطالب
```sql
SELECT u.full_name, COUNT(s.id) as total_submissions, 
       AVG(s.score) as average_score
FROM users u
LEFT JOIN submissions s ON u.id = s.user_id
GROUP BY u.id, u.full_name;
```

### 2. عرض مهام نشطة
```sql
SELECT m.id, m.objective, m.status, COUNT(t.id) as total_tasks,
       SUM(CASE WHEN t.status = 'SUCCESS' THEN 1 ELSE 0 END) as completed_tasks
FROM missions m
LEFT JOIN tasks t ON m.id = t.mission_id
WHERE m.status IN ('RUNNING', 'PLANNED')
GROUP BY m.id;
```

### 3. تحليل أداء الذكاء الاصطناعي
```sql
SELECT DATE(m.created_at) as date, 
       COUNT(*) as total_missions,
       SUM(CASE WHEN m.status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
       AVG(m.total_cost_usd) as avg_cost
FROM missions m
GROUP BY DATE(m.created_at)
ORDER BY date DESC;
```

---

## 🔍 الأدوات المساعدة (Helper Tools)

### عرض جميع الجداول
```bash
python3 list_database_tables.py
```

### التحقق من حالة الهجرات
```bash
python3 check_migrations_status.py
```

### إدارة قاعدة البيانات من الويب
```
http://localhost:5000/admin/database
```

---

## 📚 المراجع (References)

- `DATABASE_MANAGEMENT.md` - دليل شامل لإدارة قاعدة البيانات
- `DATABASE_GUIDE_AR.md` - دليل قاعدة البيانات بالعربية
- `DATABASE_TABLES_README_AR.md` - دليل استخدام السكريبتات
- `DATABASE_TABLES_OUTPUT_EXAMPLE.md` - أمثلة على المخرجات
- `app/models.py` - تعريفات النماذج الكاملة

---

**الإصدار**: 1.0.0  
**التاريخ**: 2024  
**المؤلف**: CogniForge System  
**آخر تحديث**: أكتوبر 2024
