# app/api/developer_portal_routes.py
# ======================================================================================
# ==    SUPERHUMAN DEVELOPER PORTAL API ROUTES (v1.0)                              ==
# ======================================================================================

from flask import Blueprint, current_app, jsonify, request

from app.middleware.decorators import monitor_performance, rate_limit, require_jwt_auth
from app.services.api_developer_portal_service import (
    SDKLanguage,
    TicketPriority,
    get_developer_portal_service,
)

# Create blueprint
api_bp = Blueprint("developer_portal_api", __name__, url_prefix="/api")


# ======================================================================================
# API KEY MANAGEMENT
# ======================================================================================


@api_bp.route("/developer/api-keys", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def create_api_key():
    """
    Create a new API key

    Request Body:
    {
        "developer_id": "dev_123",
        "name": "Production Key",
        "scopes": ["read", "write"],
        "expires_in_days": 365,
        "metadata": {}
    }
    """
    try:
        data = request.get_json()

        if not data or "developer_id" not in data or "name" not in data:
            return (
                jsonify({"status": "error", "message": "developer_id and name are required"}),
                400,
            )

        service = get_developer_portal_service()

        api_key = service.create_api_key(
            developer_id=data["developer_id"],
            name=data["name"],
            scopes=data.get("scopes"),
            expires_in_days=data.get("expires_in_days"),
            metadata=data.get("metadata"),
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "key_id": api_key.key_id,
                        "key_value": api_key.key_value,  # Only shown once
                        "name": api_key.name,
                        "scopes": api_key.scopes,
                        "created_at": api_key.created_at.isoformat(),
                        "expires_at": (
                            api_key.expires_at.isoformat() if api_key.expires_at else None
                        ),
                    },
                    "message": "API key created successfully. Save the key_value securely - it will not be shown again.",
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating API key: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to create API key"}), 500


@api_bp.route("/developer/api-keys/<key_id>/revoke", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def revoke_api_key(key_id: str):
    """
    Revoke an API key

    Request Body:
    {
        "reason": "Security breach"
    }
    """
    try:
        data = request.get_json()
        reason = data.get("reason", "Revoked by user") if data else "Revoked by user"

        service = get_developer_portal_service()
        success = service.revoke_api_key(key_id, reason)

        if not success:
            return jsonify({"status": "error", "message": "API key not found"}), 404

        return jsonify({"status": "success", "message": "API key revoked successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error revoking API key: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to revoke API key"}), 500


@api_bp.route("/developer/api-keys/validate", methods=["POST"])
@rate_limit
@monitor_performance
def validate_api_key():
    """
    Validate an API key

    Request Body:
    {
        "api_key": "sk_live_..."
    }
    """
    try:
        data = request.get_json()

        if not data or "api_key" not in data:
            return jsonify({"status": "error", "message": "api_key is required"}), 400

        service = get_developer_portal_service()
        api_key = service.validate_api_key(data["api_key"])

        if not api_key:
            return jsonify({"status": "error", "message": "Invalid or expired API key"}), 401

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "valid": True,
                        "key_id": api_key.key_id,
                        "developer_id": api_key.developer_id,
                        "scopes": api_key.scopes,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error validating API key: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to validate API key"}), 500


# ======================================================================================
# SUPPORT TICKETS
# ======================================================================================


@api_bp.route("/developer/tickets", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def create_support_ticket():
    """
    Create a support ticket

    Request Body:
    {
        "developer_id": "dev_123",
        "title": "API returns 500 error",
        "description": "When calling /api/users...",
        "category": "technical",
        "priority": "medium"
    }
    """
    try:
        data = request.get_json()

        required_fields = ["developer_id", "title", "description", "category"]
        if not data or not all(field in data for field in required_fields):
            return (
                jsonify(
                    {"status": "error", "message": f"Required fields: {', '.join(required_fields)}"}
                ),
                400,
            )

        service = get_developer_portal_service()

        # Convert priority string to enum
        priority_str = data.get("priority", "medium").upper()
        try:
            priority = TicketPriority[priority_str]
        except KeyError:
            priority = TicketPriority.MEDIUM

        ticket = service.create_ticket(
            developer_id=data["developer_id"],
            title=data["title"],
            description=data["description"],
            category=data["category"],
            priority=priority,
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "ticket_id": ticket.ticket_id,
                        "title": ticket.title,
                        "status": ticket.status.value,
                        "priority": ticket.priority.value,
                        "created_at": ticket.created_at.isoformat(),
                    },
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating support ticket: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to create support ticket"}), 500


@api_bp.route("/developer/tickets/<ticket_id>/messages", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def add_ticket_message(ticket_id: str):
    """
    Add a message to a ticket

    Request Body:
    {
        "author_id": "dev_123",
        "content": "Here's more information...",
        "is_staff": false
    }
    """
    try:
        data = request.get_json()

        if not data or "author_id" not in data or "content" not in data:
            return (
                jsonify({"status": "error", "message": "author_id and content are required"}),
                400,
            )

        service = get_developer_portal_service()
        success = service.add_ticket_message(
            ticket_id=ticket_id,
            author_id=data["author_id"],
            content=data["content"],
            is_staff=data.get("is_staff", False),
        )

        if not success:
            return jsonify({"status": "error", "message": "Ticket not found"}), 404

        return jsonify({"status": "success", "message": "Message added successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error adding ticket message: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to add ticket message"}), 500


@api_bp.route("/developer/tickets/<ticket_id>/resolve", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def resolve_ticket(ticket_id: str):
    """
    Resolve a support ticket

    Request Body:
    {
        "resolution": "Issue resolved by updating API endpoint"
    }
    """
    try:
        data = request.get_json()

        if not data or "resolution" not in data:
            return jsonify({"status": "error", "message": "resolution is required"}), 400

        service = get_developer_portal_service()
        success = service.resolve_ticket(ticket_id, data["resolution"])

        if not success:
            return jsonify({"status": "error", "message": "Ticket not found"}), 404

        return jsonify({"status": "success", "message": "Ticket resolved successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Error resolving ticket: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to resolve ticket"}), 500


# ======================================================================================
# SDK GENERATION
# ======================================================================================


@api_bp.route("/developer/sdks", methods=["GET"])
@rate_limit
@monitor_performance
def list_available_sdks():
    """List all available SDKs"""
    try:
        service = get_developer_portal_service()
        sdks = service.get_available_sdks()

        return jsonify({"status": "success", "data": {"sdks": sdks, "total": len(sdks)}}), 200

    except Exception as e:
        current_app.logger.error(f"Error listing SDKs: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve SDKs"}), 500


@api_bp.route("/developer/sdks/generate", methods=["POST"])
@require_jwt_auth
@rate_limit
@monitor_performance
def generate_sdk():
    """
    Generate an SDK

    Request Body:
    {
        "language": "python",
        "api_version": "v1"
    }
    """
    try:
        data = request.get_json()

        if not data or "language" not in data:
            return jsonify({"status": "error", "message": "language is required"}), 400

        # Convert language string to enum
        try:
            language = SDKLanguage[data["language"].upper()]
        except KeyError:
            return (
                jsonify(
                    {"status": "error", "message": f"Unsupported language: {data['language']}"}
                ),
                400,
            )

        service = get_developer_portal_service()
        sdk = service.generate_sdk(language=language, api_version=data.get("api_version", "v1"))

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "sdk_id": sdk.sdk_id,
                        "language": sdk.language.value,
                        "version": sdk.version,
                        "package_url": sdk.package_url,
                        "documentation_url": sdk.documentation_url,
                        "source_code": sdk.source_code,
                        "examples": sdk.examples,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating SDK: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to generate SDK"}), 500


# ======================================================================================
# DEVELOPER DASHBOARD
# ======================================================================================


@api_bp.route("/developer/<developer_id>/dashboard", methods=["GET"])
@require_jwt_auth
@rate_limit
@monitor_performance
def get_developer_dashboard(developer_id: str):
    """Get developer dashboard data"""
    try:
        service = get_developer_portal_service()
        dashboard = service.get_developer_dashboard(developer_id)

        return jsonify({"status": "success", "data": dashboard}), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving developer dashboard: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to retrieve developer dashboard"}),
            500,
        )


# ======================================================================================
# DOCUMENTATION
# ======================================================================================


@api_bp.route("/developer/docs/examples", methods=["GET"])
@rate_limit
@monitor_performance
def get_code_examples():
    """
    Get code examples

    Query Parameters:
    - language: Filter by language (optional)
    - endpoint: Filter by endpoint (optional)
    """
    try:
        service = get_developer_portal_service()

        language_filter = request.args.get("language")
        endpoint_filter = request.args.get("endpoint")

        # Get all examples
        examples = []
        for example in service.code_examples.values():
            # Apply filters
            if language_filter and example.language.value != language_filter.lower():
                continue
            if endpoint_filter and example.endpoint != endpoint_filter:
                continue

            examples.append(
                {
                    "example_id": example.example_id,
                    "title": example.title,
                    "description": example.description,
                    "language": example.language.value,
                    "code": example.code,
                    "endpoint": example.endpoint,
                    "tags": example.tags,
                    "difficulty": example.difficulty,
                }
            )

        return (
            jsonify({"status": "success", "data": {"examples": examples, "total": len(examples)}}),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error retrieving code examples: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to retrieve code examples"}), 500
