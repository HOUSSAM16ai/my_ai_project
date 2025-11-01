# 📚 دليل أسلوب API - CogniForge API Style Guide

> **نسخة:** 1.0.0  
> **تاريخ التحديث:** 2025-01-15  
> **الحالة:** نشط (Active)

---

## 🎯 المبادئ الأساسية | Core Principles

### 1. العقد أولاً (Contract-First)
- **صمم العقد قبل الكود** - استخدم OpenAPI/AsyncAPI قبل كتابة أي تطبيق
- **العقد هو مصدر الحقيقة الوحيد** - جميع الوثائق والشيفرة والاختبارات تُولّد من العقد
- **المراجعة الإلزامية** - كل عقد يجب أن يمر بمراجعة API Review Board

### 2. التوافق الخلفي (Backward Compatibility)
- **لا تغييرات كسّارة** - ممنوع كسر العملاء الحاليين
- **الإصدارات الدلالية** - استخدم Semantic Versioning (semver)
- **سياسة الإيقاف الواضحة** - أعلن عن الإيقاف مع فترة سماح واضحة

### 3. الأمان أولاً (Security First)
- **Zero Trust** - لا تثق بأي شيء، تحقق من كل شيء
- **OAuth 2.1/OIDC** - استخدم معايير المصادقة الحديثة
- **أقل الامتيازات** - امنح فقط الصلاحيات الضرورية

### 4. قابلية الملاحظة (Observability)
- **افتراضياً** - كل طلب يجب أن يكون قابلاً للتتبع
- **معرفات الارتباط** - استخدم X-Request-Id و X-Correlation-Id
- **سجلات منظمة** - JSON structured logs

### 5. تجربة المطور (Developer Experience)
- **توثيق ممتاز** - واضح، شامل، بأمثلة عملية
- **أمثلة واقعية** - لكل endpoint وسيناريو
- **SDKs رسمية** - للغات الرئيسية

---

## 🏗️ بنية API | API Structure

### تنسيق المسارات (Path Formatting)

#### ✅ القواعد الأساسية
```
✓ استخدم kebab-case:           /user-accounts
✓ صيغة الجمع للمجموعات:       /accounts
✓ تضمين الإصدار:               /v1/accounts
✓ لا trailing slash:           /accounts (not /accounts/)
✓ استخدم الأفعال للإجراءات:    /accounts/{id}/activate
```

#### ❌ تجنب
```
✗ camelCase:                   /userAccounts
✗ snake_case:                  /user_accounts
✗ صيغة المفرد للمجموعات:      /account
✗ بدون إصدار:                 /accounts
```

#### أمثلة كاملة
```
GET    /v1/accounts                    # قائمة الحسابات
POST   /v1/accounts                    # إنشاء حساب
GET    /v1/accounts/{accountId}        # حساب محدد
PATCH  /v1/accounts/{accountId}        # تحديث جزئي
DELETE /v1/accounts/{accountId}        # حذف حساب
POST   /v1/accounts/{accountId}/close  # إجراء مخصص
GET    /v1/accounts/{accountId}/transactions  # موارد فرعية
```

### الإصدارات (Versioning)

#### استراتيجية الإصدار
- **في المسار (Path Versioning)**: `/v1/`, `/v2/` (مفضّل)
- **في الرأس (Header Versioning)**: `Accept: application/vnd.cogniforge.v2+json` (متقدم)
- **رقم الإصدار**: أرقام صحيحة فقط (v1, v2, v3)

#### سياسة الإيقاف (Deprecation Policy)
```yaml
# في OpenAPI Spec
deprecated: true
x-sunset-date: "2025-12-31"
x-deprecation-notice: |
  This endpoint will be removed on December 31, 2025.
  Please migrate to /v2/accounts
x-migration-guide: "https://docs.cogniforge.com/migration/v1-to-v2"
```

#### رؤوس الإيقاف (Sunset Headers)
```http
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Deprecation: Tue, 1 Jan 2025 00:00:00 GMT
Link: <https://docs.cogniforge.com/migration>; rel="deprecation"
```

---

## 📝 أنماط الطلبات والاستجابات | Request/Response Patterns

### تنسيق JSON

#### القواعد
- **UTF-8 دائماً**
- **camelCase للخصائص**: `firstName`, `createdAt`
- **ISO 8601 للتواريخ**: `2025-01-15T10:30:00.000Z`
- **أصغر وحدة عملة للأموال**: `5000` (= $50.00)
- **رموز العملات ISO 4217**: `USD`, `EUR`, `SAR`

#### مثال طلب
```json
{
  "name": "أحمد محمد",
  "type": "individual",
  "currency": "USD",
  "metadata": {
    "customerId": "cust_123456",
    "source": "web"
  }
}
```

#### مثال استجابة
```json
{
  "id": "acc_1a2b3c4d",
  "name": "أحمد محمد",
  "type": "individual",
  "status": "active",
  "balance": 10000,
  "currency": "USD",
  "createdAt": "2025-01-15T10:30:00.000Z",
  "updatedAt": "2025-01-20T14:45:00.000Z"
}
```

### أكواد الحالة HTTP (HTTP Status Codes)

#### استخدامات قياسية
```
2xx - نجاح (Success)
  200 OK              - استرجاع/تحديث ناجح
  201 Created         - إنشاء ناجح (مع Location header)
  202 Accepted        - طلب مقبول للمعالجة اللاحقة
  204 No Content      - نجاح بدون محتوى (DELETE)

4xx - أخطاء العميل (Client Errors)
  400 Bad Request     - طلب غير صحيح
  401 Unauthorized    - مصادقة مطلوبة
  403 Forbidden       - غير مصرح (authorized but not allowed)
  404 Not Found       - المورد غير موجود
  409 Conflict        - تضارب (idempotency key reuse)
  422 Unprocessable   - خطأ في التحقق
  429 Too Many        - تجاوز الحد

5xx - أخطاء الخادم (Server Errors)
  500 Internal Error  - خطأ عام في الخادم
  502 Bad Gateway     - مشكلة في الخدمة الخلفية
  503 Service Unavailable - صيانة/حمل زائد
  504 Gateway Timeout - انتهت مهلة الخدمة الخلفية
```

### معالجة الأخطاء (Error Handling)

#### استخدام RFC 7807 Problem Details
```json
{
  "type": "https://api.cogniforge.com/errors/rate-limited",
  "title": "Rate Limited",
  "status": 429,
  "detail": "تم تجاوز حد المعدل. لديك 600 طلب/دقيقة. الرجاء المحاولة بعد 45 ثانية.",
  "instance": "/v1/accounts",
  "requestId": "req_1a2b3c4d5e6f",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "retryAfter": 45
}
```

#### نوع المحتوى
```http
Content-Type: application/problem+json; charset=utf-8
```

#### أخطاء التحقق (Validation Errors)
```json
{
  "type": "https://api.cogniforge.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "فشل التحقق من البيانات المدخلة",
  "errors": [
    {
      "field": "email",
      "message": "البريد الإلكتروني غير صالح",
      "code": "INVALID_EMAIL"
    },
    {
      "field": "amount",
      "message": "المبلغ يجب أن يكون أكبر من صفر",
      "code": "AMOUNT_TOO_LOW"
    }
  ]
}
```

---

## 🔄 التصفح والترشيح (Pagination & Filtering)

### التصفح بالمؤشر (Cursor-Based Pagination) - مفضّل

#### الطلب
```http
GET /v1/accounts?cursor=eyJpZCI6MTIzNDU2fQ==&limit=50
```

#### الاستجابة
```json
{
  "data": [
    { "id": "acc_1", "name": "Account 1" },
    { "id": "acc_2", "name": "Account 2" }
  ],
  "pagination": {
    "nextCursor": "eyJpZCI6MTIzNTA2fQ==",
    "previousCursor": "eyJpZCI6MTIzNDA2fQ==",
    "hasMore": true,
    "count": 50
  }
}
```

#### المعاملات القياسية
- `cursor` - مؤشر الصفحة (base64 encoded)
- `limit` - عدد العناصر (default: 50, max: 200)
- `hasMore` - هل توجد صفحات إضافية

### الترشيح (Filtering)

#### بنية الترشيح
```http
GET /v1/accounts?filter[status]=active&filter[createdAfter]=2025-01-01T00:00:00Z
```

#### معاملات الترشيح القياسية
```
filter[field]=value           # تساوي
filter[field.gt]=value        # أكبر من
filter[field.gte]=value       # أكبر من أو يساوي
filter[field.lt]=value        # أصغر من
filter[field.lte]=value       # أصغر من أو يساوي
filter[field.in]=val1,val2    # ضمن القائمة
```

### الترتيب (Sorting)

```http
GET /v1/accounts?sort=createdAt        # تصاعدي
GET /v1/accounts?sort=-createdAt       # تنازلي
GET /v1/accounts?sort=name,-createdAt  # متعدد
```

### الحقول المتناثرة (Sparse Fieldsets)

```http
GET /v1/accounts?fields=id,name,status,createdAt
```

---

## 🔐 الأمان والمصادقة | Security & Authentication

### OAuth 2.1 / OIDC

#### تدفق Authorization Code (للمستخدمين)
```http
# 1. طلب الترخيص
GET /oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://your-app.com/callback&
  scope=read write&
  state=random_state_string

# 2. تبديل الكود برمز وصول
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
redirect_uri=https://your-app.com/callback&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET

# 3. استخدام رمز الوصول
GET /v1/accounts
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

#### تدفق Client Credentials (للتطبيقات)
```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
scope=read write
```

#### JWT Access Tokens
```json
{
  "iss": "https://auth.cogniforge.com",
  "sub": "user_1a2b3c4d",
  "aud": "https://api.cogniforge.com",
  "exp": 1735830000,
  "iat": 1735826400,
  "scope": "read write payments:write",
  "tenant_id": "tenant_xyz"
}
```

### النطاقات (Scopes)

#### نطاقات قياسية
```
read                - قراءة الموارد العامة
write               - كتابة الموارد العامة
admin               - صلاحيات إدارية
accounts:read       - قراءة الحسابات
accounts:write      - كتابة الحسابات
payments:read       - قراءة المدفوعات
payments:write      - إنشاء المدفوعات
```

### تحديد المعدل (Rate Limiting)

#### الرؤوس
```http
X-RateLimit-Limit: 600          # الحد الأقصى للطلبات
X-RateLimit-Remaining: 573      # الطلبات المتبقية
X-RateLimit-Reset: 1735826460   # وقت إعادة التعيين (Unix timestamp)
Retry-After: 45                 # ثواني حتى المحاولة التالية
```

#### الاستجابة عند التجاوز
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735826460
Retry-After: 45

{
  "type": "https://api.cogniforge.com/errors/rate-limited",
  "title": "Rate Limited",
  "status": 429,
  "detail": "تم تجاوز حد المعدل. الرجاء المحاولة بعد 45 ثانية."
}
```

---

## ⚡ التماثل والأمان (Idempotency & Safety)

### مفتاح التماثل (Idempotency-Key)

#### متى تستخدمه
- **POST** لإنشاء الموارد (إلزامي)
- **PATCH** للتحديثات الحرجة (موصى به)
- **DELETE** للحذف الآمن (اختياري)

#### التنسيق
```http
POST /v1/payments
Idempotency-Key: idp_1a2b3c4d5e6f7g8h
Content-Type: application/json

{
  "amount": 5000,
  "currency": "USD",
  "destinationAccountId": "acc_dest123"
}
```

#### القواعد
- **طول 16-64 حرف**
- **أحرف وأرقام وشرطات**: `[a-zA-Z0-9_-]+`
- **صالح لمدة 24 ساعة**
- **إرجاع 409 Conflict** عند إعادة استخدام مفتاح مختلف
- **إرجاع نفس الاستجابة** عند إعادة استخدام نفس المفتاح

### التحديثات الشرطية (Conditional Updates)

#### استخدام ETags
```http
# 1. الحصول على ETag
GET /v1/accounts/acc_123
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"

{
  "id": "acc_123",
  "balance": 10000,
  ...
}

# 2. تحديث شرطي
PATCH /v1/accounts/acc_123
If-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"

{
  "balance": 15000
}

# 3. استجابة
HTTP/1.1 200 OK
ETag: "5d41402abc4b2a76b9719d911017c592"
```

#### فشل الشرط
```http
HTTP/1.1 412 Precondition Failed
Content-Type: application/problem+json

{
  "type": "https://api.cogniforge.com/errors/precondition-failed",
  "title": "Precondition Failed",
  "status": 412,
  "detail": "المورد تم تعديله. الرجاء إعادة جلب النسخة الأحدث."
}
```

---

## 📦 التخزين المؤقت (Caching)

### رؤوس Cache-Control

```http
# استجابات عامة قابلة للتخزين
Cache-Control: public, max-age=60

# استجابات خاصة قابلة للتخزين
Cache-Control: private, max-age=300

# غير قابل للتخزين
Cache-Control: no-store, no-cache, must-revalidate
```

### ETags

```http
# الطلب الأول
GET /v1/accounts/acc_123
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Cache-Control: private, max-age=300

# الطلب الشرطي
GET /v1/accounts/acc_123
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"

# الاستجابة
HTTP/1.1 304 Not Modified
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

---

## 🔍 قابلية الملاحظة (Observability)

### الرؤوس الإلزامية

```http
X-Request-Id: req_1a2b3c4d5e6f        # معرف فريد لكل طلب
X-Correlation-Id: corr_abc123xyz      # ربط الطلبات المترابطة
X-Tenant-Id: tenant_xyz               # معرف المستأجر (multi-tenancy)
```

### السجلات المنظمة (Structured Logs)

```json
{
  "timestamp": "2025-01-15T10:30:00.000Z",
  "level": "INFO",
  "requestId": "req_1a2b3c4d5e6f",
  "correlationId": "corr_abc123xyz",
  "method": "POST",
  "path": "/v1/accounts",
  "statusCode": 201,
  "duration": 142,
  "userId": "user_123",
  "tenantId": "tenant_xyz",
  "message": "Account created successfully"
}
```

### التتبع الموزع (Distributed Tracing)

```http
# W3C Trace Context
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: cogniforge=t61rcWkgMzE
```

---

## 🌐 الأحداث المجالية (Domain Events)

### بنية الحدث (Event Structure)

```json
{
  "eventId": "evt_1a2b3c4d5e6f",
  "eventType": "account.created",
  "eventVersion": "1.0",
  "occurredAt": "2025-01-15T10:30:00.000Z",
  "correlationId": "corr_abc123xyz",
  "causationId": "evt_trigger_xyz",
  "accountId": "acc_1a2b3c4d",
  "accountType": "individual",
  "currency": "USD",
  "metadata": {
    "source": "web_signup"
  }
}
```

### أنواع الأحداث القياسية

```
# نطاق الحسابات
account.created
account.updated
account.suspended
account.closed

# نطاق المدفوعات
payment.initiated
payment.processing
payment.settled
payment.failed
payment.refunded

# نطاق المستخدمين
user.registered
user.verified
user.login
```

---

## 📊 المقاييس والـ SLOs | Metrics & SLOs

### مقاييس RED

```
Rate      - عدد الطلبات/ثانية
Error     - معدل الأخطاء (%)
Duration  - زمن الاستجابة (P50, P95, P99)
```

### أهداف مستوى الخدمة (SLOs)

```yaml
# Core APIs
availability: 99.9%      # توفر 99.9%
p95_latency: < 100ms     # P95 أقل من 100ms
error_rate: < 0.1%       # معدل خطأ أقل من 0.1%

# Critical APIs (Payments)
availability: 99.95%
p95_latency: < 50ms
error_rate: < 0.05%
```

---

## 🚀 أفضل الممارسات | Best Practices

### ✅ افعل (DO)

1. **استخدم HTTPS دائماً** - لا HTTP في الإنتاج
2. **تحقق من المدخلات** - لا تثق بأي مدخلات
3. **أضف أمثلة** - لكل endpoint وسيناريو
4. **استخدم معرفات مبهمة** - `acc_1a2b3c4d` بدلاً من `123`
5. **أضف metadata** - للمرونة المستقبلية
6. **سجّل كل شيء** - مع structured logging
7. **راقب كل شيء** - metrics, traces, logs
8. **اختبر كل شيء** - unit, integration, contract tests
9. **وثّق كل شيء** - OpenAPI, examples, guides
10. **فكر في المستقبل** - صمم للتوسع

### ❌ لا تفعل (DON'T)

1. **لا تُرجع كلمات المرور** - أبداً في الاستجابات
2. **لا تعرض تفاصيل داخلية** - في رسائل الخطأ
3. **لا تستخدم معرفات متسلسلة** - استخدم UUIDs/ULIDs
4. **لا تكسر التوافق** - بدون إصدار جديد
5. **لا تنسى التوثيق** - وثّق كل تغيير
6. **لا تتجاهل الأمان** - اتبع OWASP API Top 10
7. **لا تنسى rate limiting** - احمِ من الإساءة
8. **لا تخزن PII بدون تشفير** - GDPR/CCPA compliance
9. **لا تستخدم GET للتغييرات** - استخدم الأفعال المناسبة
10. **لا تتجاهل الأداء** - راقب وحسّن

---

## 📋 قائمة التحقق | Checklist

### قبل إطلاق API جديد

- [ ] تم تصميم العقد (OpenAPI/AsyncAPI)
- [ ] مراجعة API Review Board
- [ ] Linting passed (Spectral)
- [ ] لا تغييرات كسّارة
- [ ] أمثلة كاملة
- [ ] توثيق كامل
- [ ] Unit tests
- [ ] Integration tests
- [ ] Contract tests
- [ ] Performance tests
- [ ] Security scan (OWASP)
- [ ] Rate limiting configured
- [ ] Monitoring setup
- [ ] Alerts configured
- [ ] Developer portal updated
- [ ] SDK generated
- [ ] Migration guide (if breaking)
- [ ] Changelog updated

---

## 🔗 مراجع | References

### المعايير
- [RFC 7807 - Problem Details](https://tools.ietf.org/html/rfc7807)
- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect](https://openid.net/connect/)
- [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0)
- [AsyncAPI 2.6](https://www.asyncapi.com/docs/reference/specification/v2.6.0)
- [JSON:API](https://jsonapi.org/)

### أفضل الممارسات
- [Google API Design Guide](https://cloud.google.com/apis/design)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

---

**🌟 Built with ❤️ by CogniForge Team**

*هذا الدليل حي ويتطور. نرحب بالمساهمات والاقتراحات.*
