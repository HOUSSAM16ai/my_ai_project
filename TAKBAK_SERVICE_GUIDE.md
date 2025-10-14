# 🎯 Takbak Service - خدمة الطبقات التنظيمية

## نظرة عامة | Overview

خدمة Takbak (الطبقات) هي ميزة جديدة في منصة CogniForge التعليمية تتيح إدارة المحتوى بطريقة هرمية ومنظمة.

The Takbak (Layers) service is a new feature in the CogniForge educational platform that enables hierarchical and organized content management.

## الميزات | Features

✅ **إدارة الطبقات الهرمية** - Create and manage hierarchical layer structures  
✅ **واجهة برمجية RESTful** - Complete REST API with CRUD operations  
✅ **دعم البيانات الوصفية** - Rich metadata support for each layer  
✅ **التنظيم المرن** - Flexible organization with parent-child relationships  
✅ **الاستعلامات المتقدمة** - Advanced querying and path tracking  

## التثبيت والإعداد | Installation & Setup

الميزة مدمجة بالفعل في المشروع. ما عليك سوى تشغيل التطبيق:

The feature is already integrated into the project. Simply run the application:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
flask run
```

## واجهة برمجة التطبيقات | API Endpoints

### 1. Health Check
```http
GET /api/v1/takbak/health
```

**Response:**
```json
{
  "ok": true,
  "service": "takbak",
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Create Layer | إنشاء طبقة
```http
POST /api/v1/takbak/layers
Content-Type: application/json

{
  "layer_id": "intro-course",
  "name": "Introduction Course",
  "description": "Beginner level course",
  "parent_id": null,
  "metadata": {
    "level": "beginner",
    "duration": "4 weeks"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": "intro-course",
    "name": "Introduction Course",
    "description": "Beginner level course",
    "parent_id": null,
    "metadata": {
      "level": "beginner",
      "duration": "4 weeks"
    },
    "created_at": "2025-10-14T18:00:00",
    "children": []
  },
  "message": "Layer created successfully"
}
```

### 3. List Layers | قائمة الطبقات
```http
GET /api/v1/takbak/layers?parent_id=intro-course&include_children=true
```

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": "lesson-1",
      "name": "First Lesson",
      "description": "Introduction to basics",
      "parent_id": "intro-course",
      "children": []
    }
  ],
  "count": 1
}
```

### 4. Get Layer | الحصول على طبقة
```http
GET /api/v1/takbak/layers/{layer_id}
```

### 5. Update Layer | تحديث طبقة
```http
PUT /api/v1/takbak/layers/{layer_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "metadata": {
    "new_field": "new_value"
  }
}
```

### 6. Delete Layer | حذف طبقة
```http
DELETE /api/v1/takbak/layers/{layer_id}?cascade=true
```

**Parameters:**
- `cascade` (boolean): If true, deletes all child layers recursively

### 7. Get Hierarchy | الحصول على الهيكل الهرمي
```http
GET /api/v1/takbak/hierarchy?root_id=intro-course
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": "intro-course",
    "name": "Introduction Course",
    "children": [
      {
        "id": "lesson-1",
        "name": "First Lesson",
        "children": []
      }
    ]
  }
}
```

### 8. Get Layer Path | المسار من الجذر
```http
GET /api/v1/takbak/layers/{layer_id}/path
```

**Response:**
```json
{
  "ok": true,
  "data": [
    {"id": "intro-course", "name": "Introduction Course", "description": "..."},
    {"id": "lesson-1", "name": "First Lesson", "description": "..."},
    {"id": "topic-1", "name": "First Topic", "description": "..."}
  ],
  "depth": 3
}
```

## أمثلة الاستخدام | Usage Examples

### مثال 1: إنشاء هيكل تعليمي | Example 1: Creating Educational Structure

```python
import requests

base_url = "http://localhost:5000/api/v1/takbak"

# Create main course
course = {
    "layer_id": "python-101",
    "name": "Python Programming 101",
    "description": "Introduction to Python"
}
response = requests.post(f"{base_url}/layers", json=course)

# Create lessons
lesson1 = {
    "layer_id": "python-101-lesson1",
    "name": "Variables and Data Types",
    "parent_id": "python-101"
}
requests.post(f"{base_url}/layers", json=lesson1)

# Get complete hierarchy
hierarchy = requests.get(f"{base_url}/hierarchy?root_id=python-101")
print(hierarchy.json())
```

### مثال 2: التنقل في الهيكل | Example 2: Navigating Structure

```python
# Get path to specific lesson
path = requests.get(f"{base_url}/layers/python-101-lesson1/path")
print("Path:", path.json()["data"])

# List all children of a course
children = requests.get(f"{base_url}/layers?parent_id=python-101")
print("Children:", children.json()["data"])
```

### مثال 3: تحديث وحذف | Example 3: Update and Delete

```python
# Update layer
update_data = {
    "name": "Updated Lesson Name",
    "metadata": {"difficulty": "easy"}
}
requests.put(f"{base_url}/layers/python-101-lesson1", json=update_data)

# Delete with cascade
requests.delete(f"{base_url}/layers/python-101?cascade=true")
```

## الاختبارات | Testing

تم توفير مجموعة اختبارات شاملة:

A comprehensive test suite is provided:

```bash
# Run all tests
pytest tests/test_takbak_service.py -v

# Run with coverage
pytest tests/test_takbak_service.py --cov=app.services.takbak_service

# Run specific test
pytest tests/test_takbak_service.py::TestTakbakService::test_create_layer -v
```

## حالات الاستخدام | Use Cases

### 1. تنظيم المحتوى التعليمي | Educational Content Organization
- تنظيم الدورات → الوحدات → الدروس → المواضيع
- Courses → Modules → Lessons → Topics

### 2. هيكلة المشاريع | Project Structuring
- المشروع → المراحل → المهام → المهام الفرعية
- Project → Phases → Tasks → Subtasks

### 3. تصنيف الموارد | Resource Classification
- الفئات → الفئات الفرعية → العناصر
- Categories → Subcategories → Items

## الأمان | Security

🔐 **Authentication Required**: All endpoints require user authentication via `@login_required`

🛡️ **Authorization**: Ensure users have appropriate permissions before accessing layers

⚠️ **Input Validation**: All inputs are validated before processing

## الأداء | Performance

⚡ **In-Memory Storage**: Current implementation uses in-memory storage for fast access  
📊 **Scalability**: Can be extended to use database persistence  
🔄 **Caching**: Future versions will include Redis caching support  

## الخطوات التالية | Next Steps

### التحسينات المخططة | Planned Improvements

- [ ] دعم قاعدة البيانات | Database persistence support
- [ ] التخزين المؤقت | Caching layer with Redis
- [ ] البحث والتصفية | Search and filtering capabilities
- [ ] التحكم في الوصول | Access control and permissions
- [ ] التصدير والاستيراد | Export/Import functionality
- [ ] واجهة مستخدم | Web UI for layer management

## المساهمة | Contributing

نرحب بالمساهمات! يرجى اتباع دليل المساهمة في المشروع.

Contributions are welcome! Please follow the project's contribution guidelines.

## الدعم | Support

للحصول على الدعم أو الإبلاغ عن مشاكل:

For support or to report issues:

- **GitHub Issues**: [Project Issues](https://github.com/HOUSSAM16ai/my_ai_project/issues)
- **Email**: support@cogniforge.ai

## الترخيص | License

هذه الميزة جزء من مشروع CogniForge وتخضع لنفس الترخيص.

This feature is part of the CogniForge project and subject to the same license.

---

**Built with ❤️ for CogniForge**

*تم إنشاؤه بكل حب لمنصة CogniForge التعليمية*
