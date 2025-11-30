# app/blueprints/admin_blueprint.py


from app.api.routers.admin import chat_stream, get_latest_chat, list_conversations, get_conversation
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

# Explicitly register the list conversations endpoint
admin_blueprint.router.add_api_route(
    "/conversations", list_conversations, methods=["GET"], summary="List Conversations"
)

# Explicitly register the get conversation details endpoint
admin_blueprint.router.add_api_route(
    "/conversations/{conversation_id}", get_conversation, methods=["GET"], summary="Get Conversation Details"
)
