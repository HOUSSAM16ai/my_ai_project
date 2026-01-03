# 🚀 Getting Started with CogniForge APIs
# دليل البدء السريع لـ APIs منصة CogniForge

> **Quick Start Guide for Developers**  
> **دليل البدء السريع للمطورين**

[![API Style](https://img.shields.io/badge/API-Contract--First-blue)](API_STYLE_GUIDE.md)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-green)](openapi/)
[![AsyncAPI](https://img.shields.io/badge/AsyncAPI-2.6-purple)](asyncapi/)

---

## 📋 Table of Contents | جدول المحتويات

1. [Prerequisites | المتطلبات الأساسية](#prerequisites)
2. [Quick Start | البدء السريع](#quick-start)
3. [Authentication | المصادقة](#authentication)
4. [First API Call | أول استدعاء API](#first-api-call)
5. [Code Examples | أمثلة الكود](#code-examples)
6. [Troubleshooting | حل المشاكل](#troubleshooting)
7. [Next Steps | الخطوات التالية](#next-steps)

---

## 📋 Prerequisites | المتطلبات الأساسية

### Required Tools | الأدوات المطلوبة

```bash
# Python 3.12+
python --version

# Node.js 20+ (for contract validation)
node --version

# cURL or HTTPie (for API testing)
curl --version
```

### Optional Tools | أدوات اختيارية

```bash
# Spectral CLI (for contract linting)
npm install -g @stoplight/spectral-cli

# Postman or Insomnia (for API exploration)
# https://www.postman.com/downloads/
```

---

## 🚀 Quick Start | البدء السريع

### Step 1: Clone the Repository | استنساخ المستودع

```bash
git clone https://github.com/ai-for-solution-labs/my_ai_project.git
cd my_ai_project
```

### Step 2: Install Dependencies | تثبيت التبعيات

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Step 3: Configure Environment | إعداد البيئة

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - DATABASE_URL: PostgreSQL connection string
# - SECRET_KEY: Flask secret key
# - OPENROUTER_API_KEY: AI service API key (optional for basic usage)
```

### Step 4: Initialize Database | تهيئة قاعدة البيانات

```bash
# Run database migrations
flask db upgrade

# Create admin user
flask users create-admin
```

### Step 5: Start the Application | تشغيل التطبيق

```bash
# Development mode
flask run

# Production mode (Docker)
docker-compose up -d
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

## 🔐 Authentication | المصادقة

### API Key Authentication | المصادقة بمفتاح API

CogniForge APIs use API keys for authentication. Generate your API key through the admin panel or CLI.

تستخدم APIs منصة CogniForge مفاتيح API للمصادقة. قم بإنشاء مفتاح API من خلال لوحة الإدارة أو سطر الأوامر.

#### Generate API Key | إنشاء مفتاح API

**Via CLI:**
```bash
flask users create --email developer@example.com --name "Developer"
# API key will be displayed in output
```

**Via Python:**
```python
from app.services.api_first_platform_service import APIFirstPlatformService

service = APIFirstPlatformService()
api_key = service.generate_api_key(
    user_id="dev_001",
    name="Development Key",
    scopes=["read", "write"]
)

print(f"API Key: {api_key['key']}")
print(f"Key ID: {api_key['id']}")
```

#### Using API Key | استخدام مفتاح API

```bash
# HTTP Header
Authorization: Bearer sk_live_abc123xyz456

# Example cURL request
curl -H "Authorization: Bearer sk_live_abc123xyz456" \
     https://api.cogniforge.com/v1/accounts
```

---

## 🎯 First API Call | أول استدعاء API

### List Accounts | قائمة الحسابات

**Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/accounts?limit=10" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Accept: application/json"
```

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": "acc_abc123",
      "name": "Test Account",
      "type": "individual",
      "currency": "USD",
      "balance": 1000.00,
      "status": "active",
      "created_at": "2026-01-03T10:00:00Z",
      "updated_at": "2026-01-03T10:00:00Z"
    }
  ],
  "meta": {
    "limit": 10,
    "cursor": "eyJpZCI6MTIzfQ==",
    "has_more": false
  }
}
```

### Create Account | إنشاء حساب

**Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/accounts" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: unique_key_001" \
     -d '{
       "name": "New Account",
       "type": "individual",
       "currency": "USD"
     }'
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": "acc_xyz789",
    "name": "New Account",
    "type": "individual",
    "currency": "USD",
    "balance": 0.00,
    "status": "active",
    "created_at": "2026-01-03T12:00:00Z",
    "updated_at": "2026-01-03T12:00:00Z"
  }
}
```

---

## 💻 Code Examples | أمثلة الكود

### Python Example | مثال Python

```python
import requests

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "sk_live_abc123xyz456"

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# List accounts
response = requests.get(
    f"{API_BASE_URL}/accounts",
    headers=headers,
    params={"limit": 10}
)

if response.ok:
    accounts = response.json()["data"]
    for account in accounts:
        print(f"Account: {account['name']} - Balance: {account['balance']}")
else:
    print(f"Error: {response.status_code} - {response.text}")

# Create account
new_account = {
    "name": "Ahmed's Account",
    "type": "individual",
    "currency": "USD"
}

response = requests.post(
    f"{API_BASE_URL}/accounts",
    headers={**headers, "Idempotency-Key": "unique_001"},
    json=new_account
)

if response.ok:
    account = response.json()["data"]
    print(f"Created: {account['id']}")
```

### JavaScript/Node.js Example | مثال JavaScript

```javascript
const axios = require('axios');

// Configuration
const API_BASE_URL = 'http://localhost:5000/api/v1';
const API_KEY = 'sk_live_abc123xyz456';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  }
});

// List accounts
async function listAccounts() {
  try {
    const response = await api.get('/accounts', {
      params: { limit: 10 }
    });
    
    const accounts = response.data.data;
    accounts.forEach(account => {
      console.log(`Account: ${account.name} - Balance: ${account.balance}`);
    });
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Create account
async function createAccount() {
  try {
    const response = await api.post('/accounts', {
      name: "Ahmed's Account",
      type: 'individual',
      currency: 'USD'
    }, {
      headers: {
        'Idempotency-Key': 'unique_001'
      }
    });
    
    const account = response.data.data;
    console.log(`Created: ${account.id}`);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Run examples
listAccounts();
createAccount();
```

### cURL Examples | أمثلة cURL

```bash
# List accounts with filtering
curl -X GET "http://localhost:5000/api/v1/accounts?status=active&limit=20" \
     -H "Authorization: Bearer YOUR_API_KEY"

# Get specific account
curl -X GET "http://localhost:5000/api/v1/accounts/acc_abc123" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "If-None-Match: \"etag_value\""

# Update account
curl -X PATCH "http://localhost:5000/api/v1/accounts/acc_abc123" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Updated Account Name"
     }'

# Delete account (soft delete)
curl -X DELETE "http://localhost:5000/api/v1/accounts/acc_abc123" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

---

## 🔍 Troubleshooting | حل المشاكل

### Common Issues | المشاكل الشائعة

#### 1. Authentication Failed | فشل المصادقة

**Error:**
```json
{
  "ok": false,
  "error": "Invalid or expired API key"
}
```

**Solution:**
- Verify your API key is correct
- Check if the key has expired
- Ensure the key has required scopes

#### 2. Rate Limit Exceeded | تجاوز حد المعدل

**Error:**
```json
{
  "ok": false,
  "error": "Rate limit exceeded"
}
```

**Response Headers:**
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735826460
```

**Solution:**
- Wait until the rate limit resets (check X-RateLimit-Reset header)
- Implement exponential backoff
- Upgrade to a higher tier plan

#### 3. Validation Error | خطأ التحقق

**Error:**
```json
{
  "ok": false,
  "error": "Validation failed",
  "details": {
    "currency": ["Currency must be one of: USD, EUR, GBP"]
  }
}
```

**Solution:**
- Check the API documentation for required fields
- Validate your request data against the OpenAPI spec
- Use correct data types and formats

#### 4. Not Found | غير موجود

**Error:**
```json
{
  "ok": false,
  "error": "Account not found"
}
```

**Solution:**
- Verify the resource ID is correct
- Check if the resource was deleted
- Ensure you have permission to access the resource

---

## 📚 Next Steps | الخطوات التالية

### 1. Explore API Documentation | استكشف توثيق API

- **OpenAPI Specification**: [accounts-api.yaml](openapi/accounts-api.yaml)
- **API Style Guide**: [API_STYLE_GUIDE.md](API_STYLE_GUIDE.md)
- **Implementation Roadmap**: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

### 2. Try Advanced Features | جرّب الميزات المتقدمة

- **GraphQL**: Query multiple resources in a single request
- **Webhooks**: Receive real-time notifications
- **gRPC**: High-performance internal APIs
- **Event Streaming**: Subscribe to domain events

### 3. Join the Community | انضم للمجتمع

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas
- **Contributing**: Read [CONTRIBUTING.md](../../CONTRIBUTING.md)

### 4. Deploy to Production | النشر للإنتاج

- **Docker**: `docker-compose -f docker-compose.prod.yml up -d`
- **Kubernetes**: See [infra/k8s/](../../infra/k8s/)
- **Security**: Review [.env.security.example](../../.env.security.example)

---

## 📞 Support | الدعم

### Documentation | التوثيق
- 📖 [API Style Guide](API_STYLE_GUIDE.md)
- 🗺️ [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)
- 🧪 [Testing Guide](API_FIRST_TESTING_GUIDE.md)

### Help Channels | قنوات المساعدة
- 🐛 **Bug Reports**: GitHub Issues
- 💬 **Questions**: GitHub Discussions
- 📧 **Email**: support@cogniforge.com

---

## 🎉 Examples Repository | مستودع الأمثلة

Check out our examples repository for more code samples:

```bash
# Clone examples
git clone https://github.com/cogniforge/api-examples.git
cd api-examples

# Run Python examples
python examples/python/account_management.py

# Run Node.js examples
node examples/nodejs/account_management.js

# Run Go examples
go run examples/go/main.go
```

---

**🌟 Built with ❤️ by Houssam Benmerah**

*Getting started is just the beginning. Build something amazing!*  
*البدء هو مجرد البداية. ابنِ شيئًا رائعًا!*

---

## 🔗 Quick Links | روابط سريعة

- [Main README](README.md)
- [API Style Guide](API_STYLE_GUIDE.md)
- [OpenAPI Specs](openapi/)
- [AsyncAPI Specs](asyncapi/)
- [gRPC Protos](grpc/)
- [GraphQL Schema](graphql/)
- [Policies & Rules](policies/)

**Happy Coding! 🚀**  
**برمجة سعيدة! 🚀**
