# 🚀 Quick Start - CRUD RESTful API

> **Start using the world-class CRUD API in 5 minutes!**

## ✅ Prerequisites

- Python 3.12+
- PostgreSQL/Supabase database
- Git

## 🏁 Quick Setup

### 1. Clone & Install

```bash
git clone https://github.com/HOUSSAM16ai/my_ai_project.git
cd my_ai_project
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database URL and keys
```

### 3. Initialize Database

```bash
flask db upgrade
```

### 4. Create Admin User

```bash
flask users create-admin admin@example.com admin_password
```

### 5. Run Application

```bash
flask run
```

Visit: `http://localhost:5000`

## 🎯 Test the API

### Get Database Health

```bash
curl http://localhost:5000/admin/api/database/health
```

### List All Tables

```bash
curl http://localhost:5000/admin/api/database/tables
```

### Create a User

```bash
curl -X POST http://localhost:5000/admin/api/database/record/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "password": "password123"
  }'
```

### Get Users (with pagination)

```bash
curl "http://localhost:5000/admin/api/database/table/users?page=1&per_page=10"
```

### Update a User

```bash
curl -X PUT http://localhost:5000/admin/api/database/record/users/1 \
  -H "Content-Type: application/json" \
  -d '{"username": "updated_name"}'
```

### Delete a User

```bash
curl -X DELETE http://localhost:5000/admin/api/database/record/users/1
```

## 📚 Full Documentation

See [CRUD_API_GUIDE_AR.md](CRUD_API_GUIDE_AR.md) for complete documentation.

## 🌟 Features Included

✅ Full CRUD operations  
✅ Input validation with Marshmallow  
✅ Error handling middleware  
✅ CORS support  
✅ Request logging  
✅ Pagination & filtering  
✅ Health checks  
✅ API documentation  
✅ Comprehensive tests  

## 🔐 Authentication

All API endpoints require authentication. Login first:

```bash
# Login via web interface
# Or use session-based authentication
```

## 📖 Next Steps

1. Read the [full API guide](CRUD_API_GUIDE_AR.md)
2. Review the [architecture diagram](CRUD_API_GUIDE_AR.md#البنية-المعمارية--architecture)
3. Explore the [validation schemas](app/validators/schemas.py)
4. Check the [example requests](CRUD_API_GUIDE_AR.md#أمثلة-عملية--practical-examples)
5. Run the [API tests](tests/test_api_crud.py)

## 🎉 You're Ready!

Start building amazing applications with this enterprise-grade API!
