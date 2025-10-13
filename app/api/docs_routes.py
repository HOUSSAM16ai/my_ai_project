# app/api/docs_routes.py
# ======================================================================================
# ==        API DOCUMENTATION ROUTES - OPENAPI/SWAGGER                             ==
# ======================================================================================
# Serve OpenAPI specification and Swagger UI

from flask import jsonify, render_template_string

from app.api import api_bp
from app.api.openapi_spec import get_openapi_spec

# Swagger UI HTML template
SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CogniForge API Gateway - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
        .topbar {
            background-color: #1a1a1a !important;
        }
        .topbar-wrapper img {
            content: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 30"><text x="5" y="20" font-family="Arial" font-size="16" fill="white">🚀 CogniForge</text></svg>');
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/api/docs/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: true,
                showRequestHeaders: true,
                validatorUrl: null
            });
            window.ui = ui;
        };
    </script>
</body>
</html>
"""


@api_bp.route("/docs", methods=["GET"])
@api_bp.route("/docs/", methods=["GET"])
def swagger_ui():
    """Serve Swagger UI for API documentation"""
    return render_template_string(SWAGGER_UI_HTML)


@api_bp.route("/docs/openapi.json", methods=["GET"])
def openapi_spec():
    """Serve OpenAPI 3.0 specification"""
    return jsonify(get_openapi_spec())


@api_bp.route("/docs/redoc", methods=["GET"])
def redoc_ui():
    """Serve ReDoc UI for API documentation"""
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CogniForge API Gateway - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/docs/openapi.json'></redoc>
        <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return render_template_string(redoc_html)
