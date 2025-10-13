# app/api/security_routes.py
# ======================================================================================
# ==        SECURITY ROUTES - ZERO-TRUST AUTHENTICATION                            ==
# ======================================================================================
# PRIME DIRECTIVE:
#   مسارات الأمان الخارقة مع Zero-Trust Architecture
#   Superhuman security routes with Zero-Trust Architecture

from datetime import datetime, timezone

from flask import current_app, g, jsonify, request

from app.api import api_bp
from app.services.api_observability_service import monitor_performance
from app.services.api_security_service import get_security_service, rate_limit, require_jwt_auth

# ======================================================================================
# TOKEN MANAGEMENT
# ======================================================================================


@api_bp.route("/security/token/generate", methods=["POST"])
@rate_limit
@monitor_performance
def generate_token():
    """
    Generate JWT access and refresh tokens

    Request Body:
    {
        "user_id": 1,
        "scopes": ["read", "write", "admin"]
    }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        scopes = data.get("scopes", ["read"])

        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        security = get_security_service()

        # Generate access token (15 minutes)
        access_token = security.generate_access_token(user_id, scopes)

        # Generate refresh token (7 days)
        refresh_token = security.generate_refresh_token(user_id)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "access_token": access_token.token,
                        "refresh_token": refresh_token.token,
                        "token_type": "Bearer",
                        "expires_in": access_token.expires_in,
                        "scopes": scopes,
                    },
                    "message": "Tokens generated successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating token: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to generate tokens"}), 500


@api_bp.route("/security/token/refresh", methods=["POST"])
@rate_limit
@monitor_performance
def refresh_token():
    """
    Refresh access token using refresh token

    Request Body:
    {
        "refresh_token": "your_refresh_token_here"
    }
    """
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"status": "error", "message": "refresh_token is required"}), 400

        security = get_security_service()

        # Verify refresh token
        payload = security.verify_token(refresh_token)

        if not payload:
            return jsonify({"status": "error", "message": "Invalid or expired refresh token"}), 401

        # Generate new access token
        user_id = payload.get("user_id")
        scopes = payload.get("scopes", ["read"])
        access_token = security.generate_access_token(user_id, scopes)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "access_token": access_token.token,
                        "token_type": "Bearer",
                        "expires_in": access_token.expires_in,
                    },
                    "message": "Access token refreshed successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to refresh token"}), 500


@api_bp.route("/security/token/revoke", methods=["POST"])
@require_jwt_auth
@rate_limit
def revoke_token():
    """
    Revoke a JWT token

    Request Body:
    {
        "jti": "token_jti_here"
    }
    """
    try:
        data = request.get_json()
        jti = data.get("jti")

        if not jti:
            return jsonify({"status": "error", "message": "jti (JWT ID) is required"}), 400

        security = get_security_service()
        security.revoke_token(jti)

        return jsonify({"status": "success", "message": "Token revoked successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error revoking token: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to revoke token"}), 500


@api_bp.route("/security/token/verify", methods=["POST"])
@rate_limit
def verify_token():
    """
    Verify a JWT token

    Request Body:
    {
        "token": "your_token_here"
    }
    """
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"status": "error", "message": "token is required"}), 400

        security = get_security_service()
        payload = security.verify_token(token)

        if not payload:
            return (
                jsonify({"status": "error", "message": "Invalid or expired token", "valid": False}),
                401,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"valid": True, "payload": payload},
                    "message": "Token is valid",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error verifying token: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to verify token"}), 500


# ======================================================================================
# REQUEST SIGNING (Zero-Trust)
# ======================================================================================


@api_bp.route("/security/signature/verify", methods=["POST"])
@rate_limit
def verify_signature():
    """
    Verify request signature (HMAC-SHA256)

    Request Body:
    {
        "signature": "hmac_signature",
        "method": "GET",
        "path": "/api/v1/users",
        "timestamp": "2025-10-12T16:00:00Z",
        "nonce": "random_nonce"
    }
    """
    try:
        data = request.get_json()

        signature = data.get("signature")
        method = data.get("method")
        path = data.get("path")
        timestamp = data.get("timestamp")
        nonce = data.get("nonce")

        if not all([signature, method, path, timestamp, nonce]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        security = get_security_service()
        is_valid = security.verify_request_signature(signature, method, path, timestamp, nonce)

        return jsonify(
            {
                "status": "success",
                "data": {"valid": is_valid},
                "message": "Signature verified" if is_valid else "Invalid signature",
            }
        ), (200 if is_valid else 401)

    except Exception as e:
        current_app.logger.error(f"Error verifying signature: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to verify signature"}), 500


# ======================================================================================
# RATE LIMITING
# ======================================================================================


@api_bp.route("/security/rate-limit/status", methods=["GET"])
@require_jwt_auth
def get_rate_limit_status():
    """Get current rate limit status for the authenticated user"""
    try:
        security = get_security_service()
        client_id = g.get("user_id", request.remote_addr)
        status = security.get_rate_limit_status(client_id)

        return jsonify({"status": "success", "data": status}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting rate limit status: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve rate limit status"}), 500


# ======================================================================================
# AUDIT LOGS
# ======================================================================================


@api_bp.route("/security/audit-logs", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_audit_logs():
    """
    Get security audit logs

    Query Parameters:
    - limit: Number of logs to retrieve (default: 100)
    - event_type: Filter by event type
    - user_id: Filter by user ID
    - severity: Filter by severity (info, warning, error, critical)
    """
    try:
        limit = request.args.get("limit", 100, type=int)
        event_type = request.args.get("event_type")
        user_id = request.args.get("user_id", type=int)
        severity = request.args.get("severity")

        security = get_security_service()
        logs = security.get_audit_logs(
            limit=limit, event_type=event_type, user_id=user_id, severity=severity
        )

        return jsonify({"status": "success", "data": {"logs": logs, "count": len(logs)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting audit logs: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve audit logs"}), 500


@api_bp.route("/security/audit-logs", methods=["POST"])
@require_jwt_auth
@rate_limit
def create_audit_log():
    """
    Create a security audit log entry

    Request Body:
    {
        "event_type": "login_success",
        "user_id": 1,
        "severity": "info",
        "details": {"ip": "192.168.1.1"}
    }
    """
    try:
        data = request.get_json()

        security = get_security_service()
        log_id = security.log_security_event(
            event_type=data.get("event_type"),
            user_id=data.get("user_id"),
            severity=data.get("severity", "info"),
            details=data.get("details", {}),
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"log_id": log_id},
                    "message": "Audit log created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating audit log: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to create audit log"}), 500


# ======================================================================================
# IP MANAGEMENT (Whitelist/Blacklist)
# ======================================================================================


@api_bp.route("/security/ip/whitelist", methods=["GET", "POST", "DELETE"])
@require_jwt_auth
@rate_limit
def manage_ip_whitelist():
    """Manage IP whitelist"""
    try:
        security = get_security_service()

        if request.method == "GET":
            whitelist = security.get_ip_whitelist()
            return jsonify({"status": "success", "data": {"whitelist": whitelist}}), 200

        elif request.method == "POST":
            data = request.get_json()
            ip_address = data.get("ip_address")
            security.add_to_whitelist(ip_address)
            return (
                jsonify({"status": "success", "message": f"IP {ip_address} added to whitelist"}),
                201,
            )

        else:  # DELETE
            data = request.get_json()
            ip_address = data.get("ip_address")
            security.remove_from_whitelist(ip_address)
            return (
                jsonify(
                    {"status": "success", "message": f"IP {ip_address} removed from whitelist"}
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Error managing IP whitelist: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to manage IP whitelist"}), 500


@api_bp.route("/security/ip/blacklist", methods=["GET", "POST", "DELETE"])
@require_jwt_auth
@rate_limit
def manage_ip_blacklist():
    """Manage IP blacklist"""
    try:
        security = get_security_service()

        if request.method == "GET":
            blacklist = security.get_ip_blacklist()
            return jsonify({"status": "success", "data": {"blacklist": blacklist}}), 200

        elif request.method == "POST":
            data = request.get_json()
            ip_address = data.get("ip_address")
            security.add_to_blacklist(ip_address)
            return (
                jsonify({"status": "success", "message": f"IP {ip_address} added to blacklist"}),
                201,
            )

        else:  # DELETE
            data = request.get_json()
            ip_address = data.get("ip_address")
            security.remove_from_blacklist(ip_address)
            return (
                jsonify(
                    {"status": "success", "message": f"IP {ip_address} removed from blacklist"}
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Error managing IP blacklist: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to manage IP blacklist"}), 500


# ======================================================================================
# SECURITY HEALTH CHECK
# ======================================================================================


@api_bp.route("/security/health", methods=["GET"])
def security_health():
    """Security service health check"""
    try:
        security = get_security_service()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "status": "healthy",
                        "features": {
                            "jwt_tokens": "active",
                            "request_signing": "active",
                            "rate_limiting": "active",
                            "audit_logging": "active",
                            "ip_filtering": "active",
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Security health check failed: {str(e)}")
        return jsonify({"status": "error", "message": "Security service unhealthy"}), 503
