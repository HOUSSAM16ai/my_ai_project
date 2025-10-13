# ======================================================================================
# ==                    SWAGGER/OPENAPI INTEGRATION (v1.0)                           ==
# ======================================================================================
# PRIME DIRECTIVE:
#   تكامل Swagger/OpenAPI خارق - Enterprise Swagger/OpenAPI integration
#   ✨ المميزات:
#   - Auto-generated API documentation
#   - Interactive API explorer
#   - Request/response examples
#   - Schema validation

from flasgger import Swagger, swag_from
from flask import Flask, jsonify

from app.api_docs import get_openapi_config


def init_swagger(app: Flask):
    """
    تهيئة Swagger - Initialize Swagger documentation

    Args:
        app: Flask application instance
    """
    # Get base configuration
    config = get_openapi_config()

    # Flasgger configuration
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/api/docs/spec.json",
                "rule_filter": lambda rule: True,  # Include all rules
                "model_filter": lambda tag: True,  # Include all models
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
        "title": config["title"],
        "version": config["version"],
        "description": config["description"],
        "termsOfService": config["termsOfService"],
        "contact": config["contact"],
        "license": config["license"],
    }

    # Initialize Swagger
    swagger = Swagger(app, config=swagger_config, template=config)

    app.logger.info("Swagger documentation initialized at /api/docs/")

    return swagger


# Example YAML specs for endpoints
HEALTH_CHECK_SPEC = """
Health check endpoint
Returns system health status and database connectivity
---
tags:
  - Health
responses:
  200:
    description: System is healthy
    schema:
      type: object
      properties:
        status:
          type: string
          example: healthy
        checks:
          type: object
          properties:
            connection:
              type: object
              properties:
                status:
                  type: string
                  example: ok
                latency_ms:
                  type: number
                  example: 12.5
"""

GET_TABLES_SPEC = """
List all database tables
Returns list of all tables with metadata and statistics
---
tags:
  - Database
security:
  - SessionAuth: []
responses:
  200:
    description: List of tables
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        tables:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
                example: users
              count:
                type: integer
                example: 42
              icon:
                type: string
                example: 👤
              category:
                type: string
                example: Core
  503:
    description: Service unavailable
"""

CREATE_RECORD_SPEC = """
Create a new record
Creates a new record in the specified table with validation
---
tags:
  - CRUD
security:
  - SessionAuth: []
parameters:
  - name: table_name
    in: path
    type: string
    required: true
    description: Name of the table
  - name: body
    in: body
    required: true
    schema:
      type: object
      example:
        email: user@example.com
        username: newuser
        password: password123
responses:
  200:
    description: Record created successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Record created successfully
        id:
          type: integer
          example: 5
  400:
    description: Validation error
  503:
    description: Service unavailable
"""

GET_RECORD_SPEC = """
Get a single record
Retrieves a single record by ID
---
tags:
  - CRUD
security:
  - SessionAuth: []
parameters:
  - name: table_name
    in: path
    type: string
    required: true
    description: Name of the table
  - name: record_id
    in: path
    type: integer
    required: true
    description: ID of the record
responses:
  200:
    description: Record found
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        data:
          type: object
  404:
    description: Record not found
"""

UPDATE_RECORD_SPEC = """
Update a record
Updates an existing record with validation
---
tags:
  - CRUD
security:
  - SessionAuth: []
parameters:
  - name: table_name
    in: path
    type: string
    required: true
    description: Name of the table
  - name: record_id
    in: path
    type: integer
    required: true
    description: ID of the record
  - name: body
    in: body
    required: true
    schema:
      type: object
      example:
        username: updated_name
responses:
  200:
    description: Record updated successfully
  400:
    description: Validation error
  404:
    description: Record not found
"""

DELETE_RECORD_SPEC = """
Delete a record
Deletes a record by ID
---
tags:
  - CRUD
security:
  - SessionAuth: []
parameters:
  - name: table_name
    in: path
    type: string
    required: true
    description: Name of the table
  - name: record_id
    in: path
    type: integer
    required: true
    description: ID of the record
responses:
  200:
    description: Record deleted successfully
  404:
    description: Record not found
"""

GET_TABLE_DATA_SPEC = """
Get table data with pagination
Retrieves paginated data from a specific table
---
tags:
  - Database
security:
  - SessionAuth: []
parameters:
  - name: table_name
    in: path
    type: string
    required: true
    description: Name of the table
  - name: page
    in: query
    type: integer
    default: 1
    description: Page number
  - name: per_page
    in: query
    type: integer
    default: 50
    description: Items per page (max 100)
  - name: search
    in: query
    type: string
    description: Search query
  - name: order_by
    in: query
    type: string
    description: Field to order by
  - name: order_dir
    in: query
    type: string
    enum: [asc, desc]
    default: asc
    description: Order direction
responses:
  200:
    description: Table data retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        table:
          type: string
          example: users
        columns:
          type: array
          items:
            type: string
        rows:
          type: array
          items:
            type: object
        total:
          type: integer
          example: 100
        page:
          type: integer
          example: 1
        per_page:
          type: integer
          example: 50
        pages:
          type: integer
          example: 2
"""
