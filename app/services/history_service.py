# app/services/history_service.py - The Akashic Records Ministry

from flask import current_app
from flask_login import current_user
from sqlalchemy import exc as sqlalchemy_exc

from app import db
from app.models import Conversation, Message


def get_recent_conversations(limit: int = 5):
    """
    Retrieves the most recent conversation objects for the current user.
    This is a pure data retrieval function.
    """
    try:
        # We ensure we only fetch conversations for the logged-in user for security.
        conversations = db.session.scalars(
            db.select(Conversation)
            .filter_by(user_id=current_user.id)
            .order_by(Conversation.start_time.desc())
            .limit(limit)
        ).all()
        return conversations
    except Exception as e:
        current_app.logger.error(
            f"Failed to fetch recent conversations for user {current_user.id}: {e}", exc_info=True
        )
        return []


def rate_message_in_db(message_id: int, rating: str):
    """
    Finds a specific message by its ID and updates its rating.
    This is the core function for the AI's learning feedback loop.
    """
    if rating not in ["good", "bad", "neutral"]:
        return {"status": "error", "message": "Invalid rating value provided."}

    try:
        # We use db.session.get for a direct, fast lookup by primary key.
        message_to_rate = db.session.get(Message, message_id)

        if not message_to_rate:
            return {"status": "error", "message": f"Message with ID {message_id} not found."}

        # --- [SECURITY PROTOCOL] ---
        # Ensure the user can only rate messages from their own conversations.
        if message_to_rate.conversation.user_id != current_user.id:
            current_app.logger.warning(
                f"SECURITY ALERT: User {current_user.id} tried to rate message {message_id} belonging to another user."
            )
            return {
                "status": "error",
                "message": "Permission denied. You can only rate your own conversations.",
            }

        message_to_rate.rating = rating
        db.session.commit()

        current_app.logger.info(f"User {current_user.id} rated message {message_id} as '{rating}'.")
        return {
            "status": "success",
            "message": f"Message {message_id} has been rated as '{rating}'.",
        }

    except sqlalchemy_exc.SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(
            f"Database error while rating message {message_id}: {e}", exc_info=True
        )
        return {"status": "error", "message": "A database error occurred."}
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Unexpected error while rating message {message_id}: {e}", exc_info=True
        )
        return {"status": "error", "message": "An unexpected error occurred."}
