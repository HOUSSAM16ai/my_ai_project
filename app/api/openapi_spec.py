# app/api/openapi_spec.py
# ======================================================================================
# ==        OPENAPI 3.0 SPECIFICATION - WORLD-CLASS API GATEWAY                     ==
# ======================================================================================
# Complete OpenAPI 3.0 specification for the API Gateway

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "CogniForge API Gateway",
        "version": "1.0.0",
        "description": "World-class API Gateway surpassing tech giants like Google, Facebook, Microsoft, OpenAI, and Apple",
        "contact": {
            "name": "CogniForge Team",
            "email": "benmerahhoussam16@gmail.com"
        },
        "license": {
            "name": "Proprietary",
            "url": "https://github.com/HOUSSAM16ai/my_ai_project"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Development server"
        },
        {
            "url": "https://api.cogniforge.com",
            "description": "Production server"
        }
    ],
    "tags": [
        {
            "name": "Health",
            "description": "Health check endpoints"
        },
        {
            "name": "Users",
            "description": "User management CRUD operations"
        },
        {
            "name": "Missions",
            "description": "Mission management CRUD operations"
        },
        {
            "name": "Tasks",
            "description": "Task management CRUD operations"
        },
        {
            "name": "Security",
            "description": "Authentication and security operations"
        },
        {
            "name": "Observability",
            "description": "Monitoring and metrics"
        },
        {
            "name": "Gateway",
            "description": "API Gateway control"
        }
    ],
    "paths": {
        "/api/v1/health": {
            "get": {
                "tags": ["Health"],
                "summary": "API health check",
                "description": "Check if the API is healthy and responsive",
                "responses": {
                    "200": {
                        "description": "API is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HealthResponse"
                                }
                            }
                        }
                    },
                    "503": {
                        "description": "API is unhealthy"
                    }
                }
            }
        },
        "/api/v1/users": {
            "get": {
                "tags": ["Users"],
                "summary": "List all users",
                "description": "Get all users with pagination, filtering, and sorting",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1},
                        "description": "Page number"
                    },
                    {
                        "name": "per_page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 20},
                        "description": "Items per page"
                    },
                    {
                        "name": "sort_by",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Field to sort by"
                    },
                    {
                        "name": "sort_order",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["asc", "desc"]},
                        "description": "Sort order"
                    },
                    {
                        "name": "email",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by email"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Users retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UsersListResponse"
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Users"],
                "summary": "Create a new user",
                "description": "Create a new user with the provided information",
                "security": [
                    {"BearerAuth": []}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/CreateUserRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Validation error"
                    },
                    "409": {
                        "description": "User already exists"
                    }
                }
            }
        },
        "/api/v1/users/{user_id}": {
            "get": {
                "tags": ["Users"],
                "summary": "Get a specific user",
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "User retrieved successfully"
                    },
                    "404": {
                        "description": "User not found"
                    }
                }
            },
            "put": {
                "tags": ["Users"],
                "summary": "Update a user",
                "security": [
                    {"BearerAuth": []}
                ],
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UpdateUserRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "User updated successfully"
                    },
                    "404": {
                        "description": "User not found"
                    }
                }
            },
            "delete": {
                "tags": ["Users"],
                "summary": "Delete a user",
                "security": [
                    {"BearerAuth": []}
                ],
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "User deleted successfully"
                    },
                    "404": {
                        "description": "User not found"
                    }
                }
            }
        },
        "/api/security/token/generate": {
            "post": {
                "tags": ["Security"],
                "summary": "Generate JWT tokens",
                "description": "Generate access and refresh tokens for authentication",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/TokenGenerateRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Tokens generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TokenResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request"
                    }
                }
            }
        },
        "/api/observability/metrics": {
            "get": {
                "tags": ["Observability"],
                "summary": "Get API metrics",
                "description": "Retrieve comprehensive API performance metrics",
                "responses": {
                    "200": {
                        "description": "Metrics retrieved successfully"
                    }
                }
            }
        }
    },
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "schemas": {
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "example": "success"
                    },
                    "message": {
                        "type": "string",
                        "example": "API is healthy"
                    },
                    "data": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "example": "healthy"
                            },
                            "database": {
                                "type": "string",
                                "example": "connected"
                            },
                            "version": {
                                "type": "string",
                                "example": "v1.0"
                            }
                        }
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    }
                }
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "username": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "is_admin": {
                        "type": "boolean"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "updated_at": {
                        "type": "string",
                        "format": "date-time"
                    }
                }
            },
            "CreateUserRequest": {
                "type": "object",
                "required": ["username", "email", "password"],
                "properties": {
                    "username": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 50
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "password": {
                        "type": "string",
                        "minLength": 8
                    },
                    "is_admin": {
                        "type": "boolean",
                        "default": False
                    }
                }
            },
            "UpdateUserRequest": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "password": {
                        "type": "string"
                    }
                }
            },
            "UsersListResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string"
                    },
                    "message": {
                        "type": "string"
                    },
                    "data": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/User"
                                }
                            },
                            "pagination": {
                                "$ref": "#/components/schemas/Pagination"
                            }
                        }
                    }
                }
            },
            "UserResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string"
                    },
                    "message": {
                        "type": "string"
                    },
                    "data": {
                        "$ref": "#/components/schemas/User"
                    }
                }
            },
            "Pagination": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer"
                    },
                    "per_page": {
                        "type": "integer"
                    },
                    "total_pages": {
                        "type": "integer"
                    },
                    "total_items": {
                        "type": "integer"
                    },
                    "has_next": {
                        "type": "boolean"
                    },
                    "has_prev": {
                        "type": "boolean"
                    }
                }
            },
            "TokenGenerateRequest": {
                "type": "object",
                "required": ["user_id"],
                "properties": {
                    "user_id": {
                        "type": "integer"
                    },
                    "scopes": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "default": ["read"]
                    }
                }
            },
            "TokenResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string"
                    },
                    "data": {
                        "type": "object",
                        "properties": {
                            "access_token": {
                                "type": "string"
                            },
                            "refresh_token": {
                                "type": "string"
                            },
                            "token_type": {
                                "type": "string",
                                "example": "Bearer"
                            },
                            "expires_in": {
                                "type": "integer",
                                "example": 900
                            }
                        }
                    }
                }
            }
        }
    }
}


def get_openapi_spec():
    """Get the OpenAPI specification"""
    return OPENAPI_SPEC
