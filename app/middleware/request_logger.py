# ======================================================================================
# ==                    REQUEST LOGGER MIDDLEWARE (v1.0)                             ==
# ======================================================================================
# PRIME DIRECTIVE:
#   تسجيل الطلبات الخارق - Enterprise request logging
#   ✨ المميزات:
#   - Request/response logging
#   - Performance monitoring
#   - Error tracking
#   - Audit trail

from flask import Flask, request, g
from datetime import datetime, timezone
import time
import json


def setup_request_logging(app: Flask):
    """
    إعداد تسجيل الطلبات - Setup request logging for the Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def log_request_start():
        """تسجيل بداية الطلب - Log request start"""
        g.start_time = time.time()
        g.request_id = f"{datetime.now(timezone.utc).timestamp()}-{id(request)}"
        
        # Log request details
        app.logger.info(
            f"[{g.request_id}] {request.method} {request.path} | "
            f"IP: {request.remote_addr} | "
            f"User-Agent: {request.user_agent.string[:50]}..."
        )
        
        # Log request body for POST/PUT/PATCH (be careful with sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            # Don't log passwords and sensitive fields
            safe_data = {
                k: v for k, v in request.json.items() 
                if k.lower() not in ['password', 'token', 'secret', 'api_key']
            }
            app.logger.debug(f"[{g.request_id}] Request body: {json.dumps(safe_data)}")
    
    @app.after_request
    def log_request_end(response):
        """تسجيل نهاية الطلب - Log request end"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            duration_ms = round(duration * 1000, 2)
            
            # Add performance headers
            response.headers['X-Request-Duration-Ms'] = str(duration_ms)
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
            
            # Log response
            log_level = 'info' if response.status_code < 400 else 'warning' if response.status_code < 500 else 'error'
            
            log_message = (
                f"[{g.request_id}] {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration_ms}ms"
            )
            
            if log_level == 'info':
                app.logger.info(log_message)
            elif log_level == 'warning':
                app.logger.warning(log_message)
            else:
                app.logger.error(log_message)
            
            # Log slow requests
            if duration_ms > 1000:  # Slower than 1 second
                app.logger.warning(
                    f"[{g.request_id}] SLOW REQUEST: {request.method} {request.path} "
                    f"took {duration_ms}ms"
                )
        
        return response
    
    @app.teardown_request
    def log_request_teardown(error=None):
        """تسجيل تفكيك الطلب - Log request teardown"""
        if error:
            app.logger.error(
                f"[{getattr(g, 'request_id', 'unknown')}] Request teardown error: {error}",
                exc_info=True
            )
