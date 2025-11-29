# app/blueprints/admin_blueprint.py


from app.api.routers.admin import chat_stream, get_latest_chat
from app.blueprints import Blueprint

# Create the blueprint object
admin_blueprint = Blueprint(name="admin/api")

# Explicitly register the real get_latest_chat endpoint
admin_blueprint.router.add_api_route(
    "/chat/latest", get_latest_chat, methods=["GET"], summary="Get Latest Conversation"
)

# Explicitly register the real chat_stream endpoint
admin_blueprint.router.add_api_route(
    "/chat/stream", chat_stream, methods=["POST"], summary="Admin Chat Streaming Endpoint"
)
