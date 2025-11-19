# app/services/admin_ai_service.py
import logging
from sqlalchemy.orm import Session
from app.models import AdminConversation, AdminMessage, User

logger = logging.getLogger(__name__)

class AdminAIService:
    def create_conversation(
        self, db: Session, user: User, title: str, conversation_type: str = "general"
    ) -> AdminConversation:
        conversation = AdminConversation(
            title=title, user_id=user.id, conversation_type=conversation_type
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def get_conversation_history(self, db: Session, conversation_id: int) -> list[dict[str, str]]:
        messages = (
            db.query(AdminMessage)
            .filter(AdminMessage.conversation_id == conversation_id)
            .order_by(AdminMessage.created_at)
            .all()
        )
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def save_message(
        self,
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
    ):
        message = AdminMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        db.add(message)
        db.commit()

admin_ai_service = AdminAIService()
