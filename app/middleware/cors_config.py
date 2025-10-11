# ======================================================================================
# ==                    CORS CONFIGURATION MIDDLEWARE (v1.0)                         ==
# ======================================================================================
# PRIME DIRECTIVE:
#   تكوين CORS خارق - Enterprise CORS configuration
#   ✨ المميزات:
#   - Cross-Origin Resource Sharing support
#   - Configurable origins
#   - Support for credentials
#   - Custom headers and methods

from flask import Flask
from flask_cors import CORS


def setup_cors(app: Flask):
    """
    إعداد CORS - Setup CORS for the Flask app
    
    Args:
        app: Flask application instance
    """
    
    # CORS configuration
    cors_config = {
        'origins': [
            'http://localhost:5000',
            'http://localhost:3000',
            'http://127.0.0.1:5000',
            'http://127.0.0.1:3000',
        ],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        'allow_headers': [
            'Content-Type',
            'Authorization',
            'X-Requested-With',
            'X-API-Key',
            'Accept',
            'Origin'
        ],
        'expose_headers': [
            'Content-Type',
            'X-Total-Count',
            'X-Page',
            'X-Per-Page',
            'X-Total-Pages'
        ],
        'supports_credentials': True,
        'max_age': 3600  # 1 hour
    }
    
    # Add production origins from config
    if app.config.get('PRODUCTION_ORIGINS'):
        cors_config['origins'].extend(app.config['PRODUCTION_ORIGINS'])
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": cors_config,
        r"/admin/api/*": cors_config
    })
    
    app.logger.info(f'CORS configured with origins: {cors_config["origins"]}')
