# ======================================================================================
# ==                    API DOCUMENTATION MODULE (v1.0)                              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   توثيق API خارق احترافي - Enterprise-grade API documentation
#   ✨ المميزات:
#   - OpenAPI/Swagger specification
#   - Interactive API documentation
#   - Request/response examples
#   - Authentication documentation

from typing import Any


def get_openapi_config() -> dict[str, Any]:
    """
    تكوين OpenAPI/Swagger - OpenAPI configuration

    Returns:
        OpenAPI configuration dictionary
    """
    return {
        "title": "CogniForge API - Enterprise CRUD RESTful API",
        "version": "2.0.0",
        "description": """
# 🚀 CogniForge RESTful API Documentation

نظام API خارق احترافي يتفوق على الشركات العملاقة
**A world-class RESTful API surpassing tech giants like Google, Facebook, and Microsoft**

## 🌟 Features | المميزات

- ✅ **Complete CRUD Operations**: Create, Read, Update, Delete on all resources
- ✅ **Advanced Validation**: Marshmallow-based input validation
- ✅ **Pagination & Filtering**: Efficient data retrieval with search and sort
- ✅ **Error Handling**: Standardized error responses with detailed messages
- ✅ **Security**: Admin authentication and authorization
- ✅ **Performance**: Optimized queries with caching (5-min TTL)
- ✅ **Monitoring**: Health checks and database statistics
- ✅ **Documentation**: Auto-generated OpenAPI/Swagger docs

## 🔐 Authentication

All API endpoints require authentication. Use the admin login credentials:

```
POST /auth/login
{
  "email": "admin@example.com",
  "password": "your_password"
}
```

## 📊 Response Format

### Success Response:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "metadata": {
    "timestamp": "2025-10-11T20:32:20Z",
    "version": "2.0.0"
  }
}
```

### Error Response:
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Validation failed",
    "details": {
      "validation_errors": { ... }
    }
  }
}
```

## 🎯 Core Resources

- **Users**: User account management
- **Missions**: AI mission orchestration
- **Tasks**: Mission task management
- **Mission Plans**: Mission execution plans
- **Admin Conversations**: AI chat conversations

## 📈 Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Standard**: 100 requests per minute
- **Burst**: 200 requests per minute

## 🌍 CORS

CORS is enabled for the following origins:
- `http://localhost:5000`
- `http://localhost:3000`
- Production domains (configured per deployment)
        """,
        "termsOfService": "https://cogniforge.ai/terms",
        "contact": {
            "name": "CogniForge API Support",
            "email": "support@cogniforge.ai",
            "url": "https://cogniforge.ai/support",
        },
        "license": {"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
        "servers": [
            {"url": "http://localhost:5000", "description": "Development server"},
            {"url": "https://api.cogniforge.ai", "description": "Production server"},
        ],
        "tags": [
            {"name": "Health", "description": "System health and monitoring endpoints"},
            {"name": "Database", "description": "Database management and operations"},
            {"name": "Users", "description": "User account management"},
            {"name": "Missions", "description": "AI mission orchestration"},
            {"name": "Tasks", "description": "Mission task management"},
            {"name": "Conversations", "description": "Admin AI conversations"},
        ],
        "securityDefinitions": {
            "SessionAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "session",
                "description": "Session-based authentication using Flask-Login",
            }
        },
        "security": [{"SessionAuth": []}],
    }


def get_api_endpoints_documentation() -> dict[str, Any]:
    """
    وثائق نقاط النهاية - API endpoints documentation

    Returns:
        Documentation for all API endpoints
    """
    return {
        "health": {
            "GET /api/health": {
                "summary": "System health check",
                "description": "Get system health status and metrics",
                "tags": ["Health"],
                "responses": {
                    200: {
                        "description": "System is healthy",
                        "example": {
                            "success": True,
                            "data": {"status": "healthy", "database": "connected", "uptime": 3600},
                        },
                    }
                },
            }
        },
        "database": {
            "GET /admin/api/database/tables": {
                "summary": "List all database tables",
                "description": "Get list of all tables with metadata and statistics",
                "tags": ["Database"],
                "responses": {
                    200: {
                        "description": "List of tables",
                        "example": {
                            "status": "success",
                            "tables": [
                                {"name": "users", "count": 42, "icon": "👤", "category": "Core"}
                            ],
                        },
                    }
                },
            },
            "GET /admin/api/database/stats": {
                "summary": "Database statistics",
                "description": "Get comprehensive database statistics and metrics",
                "tags": ["Database"],
            },
            "GET /admin/api/database/health": {
                "summary": "Database health check",
                "description": "Check database connection and health status",
                "tags": ["Database"],
            },
        },
        "crud": {
            "GET /admin/api/database/table/<table_name>": {
                "summary": "Get table data",
                "description": "Retrieve paginated data from a specific table",
                "tags": ["Database"],
                "parameters": [
                    {
                        "name": "table_name",
                        "in": "path",
                        "required": True,
                        "type": "string",
                        "description": "Name of the table",
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "type": "integer",
                        "default": 1,
                        "description": "Page number",
                    },
                    {
                        "name": "per_page",
                        "in": "query",
                        "type": "integer",
                        "default": 50,
                        "description": "Items per page (max 100)",
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "type": "string",
                        "description": "Search query",
                    },
                    {
                        "name": "order_by",
                        "in": "query",
                        "type": "string",
                        "description": "Field to order by",
                    },
                    {
                        "name": "order_dir",
                        "in": "query",
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "default": "asc",
                        "description": "Order direction",
                    },
                ],
            },
            "GET /admin/api/database/record/<table_name>/<id>": {
                "summary": "Get single record",
                "description": "Retrieve a single record by ID",
                "tags": ["Database"],
            },
            "POST /admin/api/database/record/<table_name>": {
                "summary": "Create record",
                "description": "Create a new record in the specified table",
                "tags": ["Database"],
            },
            "PUT /admin/api/database/record/<table_name>/<id>": {
                "summary": "Update record",
                "description": "Update an existing record",
                "tags": ["Database"],
            },
            "DELETE /admin/api/database/record/<table_name>/<id>": {
                "summary": "Delete record",
                "description": "Delete a record by ID",
                "tags": ["Database"],
            },
        },
    }
