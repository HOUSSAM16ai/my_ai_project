# app/services/history_service.py - The Akashic Records Ministry
"""
History Service - Async-compatible service for conversation history operations.

This service was migrated from Flask to FastAPI and now properly uses
async database sessions via SQLAlchemy's async engine.
"""

import logging

from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory

logger = logging.getLogger(__name__)

async def get_recent_conversations(user_id: int, limit: int = 5) -> None:
    """
    Retrieves the most recent conversation objects for the current user.
    This is a pure data retrieval function using async database session.

    Args:
        user_id: The ID of the user whose conversations to retrieve.
        limit: Maximum number of conversations to return (default: 5).

    Returns:
        List of AdminConversation objects, or empty list on error.
    """
    from app.models import AdminConversation as Conversation

    try:
        async with async_session_factory() as session:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc(), Conversation.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            conversations = result.scalars().all()
            return list(conversations)
    except Exception as e:
        logger.error(f"Failed to fetch recent conversations for user {user_id}: {e}", exc_info=True)
        return []

async def rate_message_in_db(message_id: int, rating: str, user_id: int) -> None:
    """
    Finds a specific message by its ID and updates its rating.
    This is the core function for the AI's learning feedback loop.

    Args:
        message_id: The ID of the message to rate.
        rating: The rating value ('good', 'bad', or 'neutral').
        user_id: The ID of the user making the rating.

    Returns:
        Dict with 'status' and 'message' keys indicating success or error.
    """
    from app.models import AdminMessage as Message

    if rating not in ["good", "bad", "neutral"]:
        return {"status": "error", "message": "Invalid rating value provided."}

    try:
        async with async_session_factory() as session:
            # Fetch message with its conversation eagerly loaded for ownership check
            stmt = (
                select(Message)
                .options(selectinload(Message.conversation))
                .where(Message.id == message_id)
            )
            result = await session.execute(stmt)
            message_to_rate = result.scalar_one_or_none()

            if not message_to_rate:
                return {"status": "error", "message": f"Message with ID {message_id} not found."}

            # --- [SECURITY PROTOCOL] ---
            # Ensure the user can only rate messages from their own conversations.
            if message_to_rate.conversation.user_id != user_id:
                logger.warning(
                    f"SECURITY ALERT: User {user_id} tried to rate message {message_id} belonging to another user."
                )
                return {
                    "status": "error",
                    "message": "Permission denied. You can only rate your own conversations.",
                }

            if hasattr(message_to_rate, "rating"):
                message_to_rate.rating = rating
                await session.commit()
            else:
                logger.warning("Message model has no rating field. Skipping update.")

            logger.info(f"User {user_id} rated message {message_id} as '{rating}'.")
            return {
                "status": "success",
                "message": f"Message {message_id} has been rated as '{rating}'.",
            }

    except sqlalchemy_exc.SQLAlchemyError as e:
        logger.error(f"Database error while rating message {message_id}: {e}", exc_info=True)
        return {"status": "error", "message": "A database error occurred."}
    except Exception as e:
        logger.error(f"Unexpected error while rating message {message_id}: {e}", exc_info=True)
        return {"status": "error", "message": "An unexpected error occurred."}
