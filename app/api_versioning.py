# ======================================================================================
# ==                    API VERSIONING MODULE (v1.0)                                 ==
# ======================================================================================
# PRIME DIRECTIVE:
#   إدارة إصدارات API احترافية - Professional API versioning
#   ✨ المميزات:
#   - Version-based routing
#   - Backward compatibility
#   - Version deprecation warnings
#   - Automatic version detection

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from typing import Callable


class APIVersion:
    """مدير إصدارات API - API version manager"""
    
    SUPPORTED_VERSIONS = ['v1', 'v2']
    DEFAULT_VERSION = 'v2'
    DEPRECATED_VERSIONS = []
    
    @staticmethod
    def get_version_from_request() -> str:
        """
        استخراج رقم الإصدار من الطلب - Extract version from request
        
        Supports multiple methods:
        1. URL path: /api/v1/users
        2. Header: X-API-Version: v1
        3. Query param: ?api_version=v1
        """
        # Try URL path first
        if '/api/v' in request.path:
            parts = request.path.split('/api/')
            if len(parts) > 1:
                version_part = parts[1].split('/')[0]
                if version_part in APIVersion.SUPPORTED_VERSIONS:
                    return version_part
        
        # Try header
        header_version = request.headers.get('X-API-Version')
        if header_version in APIVersion.SUPPORTED_VERSIONS:
            return header_version
        
        # Try query param
        query_version = request.args.get('api_version')
        if query_version in APIVersion.SUPPORTED_VERSIONS:
            return query_version
        
        # Default
        return APIVersion.DEFAULT_VERSION
    
    @staticmethod
    def version_required(min_version: str = 'v1'):
        """
        ديكور للتحقق من الإصدار - Decorator to check API version
        
        Args:
            min_version: Minimum required API version
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                current_version = APIVersion.get_version_from_request()
                
                # Check if version is supported
                if current_version not in APIVersion.SUPPORTED_VERSIONS:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 400,
                            'message': 'Unsupported API version',
                            'details': {
                                'requested_version': current_version,
                                'supported_versions': APIVersion.SUPPORTED_VERSIONS,
                                'default_version': APIVersion.DEFAULT_VERSION
                            }
                        }
                    }), 400
                
                # Check if version is deprecated
                if current_version in APIVersion.DEPRECATED_VERSIONS:
                    current_app.logger.warning(
                        f"Using deprecated API version: {current_version}"
                    )
                
                # Add version to response headers
                response = f(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers['X-API-Version'] = current_version
                
                return response
            
            return decorated_function
        return decorator


def create_versioned_blueprint(name: str, version: str = 'v2') -> Blueprint:
    """
    إنشاء blueprint بإصدار محدد - Create versioned blueprint
    
    Args:
        name: Blueprint name
        version: API version
        
    Returns:
        Versioned blueprint
    """
    bp = Blueprint(
        f'{name}_{version}',
        __name__,
        url_prefix=f'/api/{version}'
    )
    
    return bp


# Example usage in routes:
# @bp.route('/users')
# @APIVersion.version_required(min_version='v1')
# def get_users():
#     return jsonify({'users': []})
