# app/services/history_service.py - The Akashic Records Ministry

import logging
from typing import Optional, Any

from sqlalchemy import exc as sqlalchemy_exc
from sqlmodel import select

# Compatibility imports - removed Flask dependencies
from app.core.database import get_session as get_db_session

def get_db():
    # Helper to get session
    from app.core.di import get_session
    return get_session()

class DBWrapper:
    @property
    def session(self):
        return get_db()

    def select(self, *args):
        return select(*args)

db = DBWrapper()


def get_recent_conversations(user_id: int, limit: int = 5):
    """
    Retrieves the most recent conversation objects for the current user.
    This is a pure data retrieval function.
    """
    from app.models import AdminConversation as Conversation
    try:
        session = db.session
        conversations = session.scalars(
            db.select(Conversation)
            .filter_by(user_id=user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        ).all()
        return conversations
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to fetch recent conversations for user {user_id}: {e}", exc_info=True
        )
        return []


def rate_message_in_db(message_id: int, rating: str, user_id: int):
    """
    Finds a specific message by its ID and updates its rating.
    This is the core function for the AI's learning feedback loop.
    """
    from app.models import AdminMessage as Message

    if rating not in ["good", "bad", "neutral"]:
        return {"status": "error", "message": "Invalid rating value provided."}

    try:
        session = db.session
        message_to_rate = session.get(Message, message_id)

        if not message_to_rate:
            return {"status": "error", "message": f"Message with ID {message_id} not found."}

        # --- [SECURITY PROTOCOL] ---
        # Ensure the user can only rate messages from their own conversations.
        if message_to_rate.conversation.user_id != user_id:
            logging.getLogger(__name__).warning(
                f"SECURITY ALERT: User {user_id} tried to rate message {message_id} belonging to another user."
            )
            return {
                "status": "error",
                "message": "Permission denied. You can only rate your own conversations.",
            }

        if hasattr(message_to_rate, 'rating'):
            message_to_rate.rating = rating
            session.commit()
        else:
             logging.getLogger(__name__).warning(f"Message model has no rating field. Skipping update.")

        logging.getLogger(__name__).info(f"User {user_id} rated message {message_id} as '{rating}'.")
        return {
            "status": "success",
            "message": f"Message {message_id} has been rated as '{rating}'.",
        }

    except sqlalchemy_exc.SQLAlchemyError as e:
        session.rollback()
        logging.getLogger(__name__).error(
            f"Database error while rating message {message_id}: {e}", exc_info=True
        )
        return {"status": "error", "message": "A database error occurred."}
    except Exception as e:
        session.rollback()
        logging.getLogger(__name__).error(
            f"Unexpected error while rating message {message_id}: {e}", exc_info=True
        )
        return {"status": "error", "message": "An unexpected error occurred."}
