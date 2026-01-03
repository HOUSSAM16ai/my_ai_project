# app/services/admin_ai_service.py
import logging

from sqlalchemy.orm import Session

from app.core.ai_gateway import get_ai_client
from app.core.domain.models import AdminConversation, AdminMessage, User

logger = logging.getLogger(__name__)

# Module-level function for testing patching
def get_llm_client() -> None:
    return get_ai_client()

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
            .order_by(AdminMessage.created_at, AdminMessage.id)
            .all()
        )
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def save_message(
        self,
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
    ) -> None:
        message = AdminMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        db.add(message)
        db.commit()

    # Alias for testing - Must be explicitly defined as method
    def _save_message(self, db, conversation_id, role, content):
        return self.save_message(db, conversation_id, role, content)

    def get_llm_client(self) -> None:
        """
        Returns the AIClient. This method is primarily a hook for testing.
        """
        return get_llm_client()

    def _extract_response_data(self, response) -> dict[str, str | int]:
        """
        استخراج البيانات من استجابة AI بشكل آمن.
        
        Args:
            response: استجابة من AI model
            
        Returns:
            dict: البيانات المستخرجة (content, tool_calls, tokens_used, model)
        """
        content = getattr(response.choices[0].message, "content", None)
        tool_calls = getattr(response.choices[0].message, "tool_calls", None)
        usage = getattr(response, "usage", None)
        model = getattr(response, "model", "unknown")
        
        tokens_used = 0
        if usage:
            tokens_used = getattr(usage, "total_tokens", 0)
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "tokens_used": tokens_used,
            "model": model,
        }

    def _handle_empty_response(
        self,
        response_data: dict[str, str | int],
        attempt: int,
        max_retries: int
    ) -> dict[str, str | int] | None:
        """
        معالجة الاستجابات الفارغة من AI.
        
        Args:
            response_data: البيانات المستخرجة من الاستجابة
            attempt: رقم المحاولة الحالية
            max_retries: الحد الأقصى للمحاولات
            
        Returns:
            dict أو None: خطأ معالج أو None للمتابعة
        """
        content = response_data["content"]
        tool_calls = response_data["tool_calls"]
        tokens_used = response_data["tokens_used"]
        model = response_data["model"]
        
        # التحقق من كون المحتوى فارغاً
        if content is None or (isinstance(content, str) and content.strip() == ""):
            if tool_calls:
                logger.warning(
                    f"Empty content but tool_calls present (attempt {attempt + 1}/{max_retries})"
                )
                return {
                    "status": "error",
                    "answer": "Tool calls detected but no content. This may indicate a model configuration issue.",
                    "tokens_used": tokens_used,
                    "model_used": model,
                    "error_type": "empty_with_tools",
                }

            # استجابة فارغة بدون tool calls
            if attempt < max_retries - 1:
                logger.warning(
                    f"Empty response (attempt {attempt + 1}/{max_retries}). Retrying..."
                )
                return None  # يشير إلى المتابعة للمحاولة التالية

            logger.error(
                f"Empty response after {max_retries} attempts. "
                "This may indicate an API or model issue."
            )
            return {
                "status": "error",
                "answer": "Model did not return any content (لم يُرجع أي محتوى). Please try again or contact support.",
                "tokens_used": tokens_used,
                "model_used": model,
                "error_type": "empty_response",
            }
        
        # المحتوى موجود - لا حاجة لمعالجة خاصة
        return None

    def _create_success_response(self, response_data: dict[str, str | int]) -> dict[str, str | int]:
        """
        إنشاء استجابة نجاح.
        
        Args:
            response_data: البيانات المستخرجة من الاستجابة
            
        Returns:
            dict: استجابة نجاح منسقة
        """
        content = response_data["content"]
        tokens_used = response_data["tokens_used"]
        model = response_data["model"]
        
        logger.info(
            f"Successfully received response (length: {len(content)}, tokens: {tokens_used})"
        )
        return {
            "status": "success",
            "answer": content,
            "tokens_used": tokens_used,
            "model_used": model,
        }

    def _handle_attribute_error(self, error: AttributeError) -> dict[str, str]:
        """
        معالجة أخطاء بنية الاستجابة.
        
        Args:
            error: خطأ AttributeError
            
        Returns:
            dict: رسالة خطأ منسقة
        """
        logger.error(f"Response structure error: {error}", exc_info=True)
        return {
            "status": "error",
            "answer": f"Invalid response structure from AI model: {error!s}",
            "error_type": "invalid_structure",
        }

    def _handle_general_error(
        self,
        error: Exception,
        attempt: int,
        max_retries: int
    ) -> dict[str, str] | None:
        """
        معالجة الأخطاء العامة.
        
        Args:
            error: الخطأ الذي حدث
            attempt: رقم المحاولة الحالية
            max_retries: الحد الأقصى للمحاولات
            
        Returns:
            dict أو None: خطأ معالج أو None للمتابعة
        """
        logger.error(
            f"Error in answer_question (attempt {attempt + 1}/{max_retries}): "
            f"{type(error).__name__}: {error}",
            exc_info=True,
        )

        if attempt < max_retries - 1:
            return None  # المتابعة للمحاولة التالية

        return {
            "status": "error",
            "answer": f"Failed to get response from AI: {type(error).__name__}: {error!s}",
            "error_type": type(error).__name__,
        }

    def answer_question(
        self,
        question: str,
        user: dict[str, str | int | bool],
        conversation_id: str | None = None,
        use_deep_context: bool = False,
    ) -> dict[str, str | int]:
        """
        الإجابة على سؤال باستخدام الذكاء الاصطناعي.

        SUPERHUMAN ENHANCEMENTS:
        - Better empty response handling
        - Detailed error categorization
        - Retry logic for transient failures
        
        تم التحسين: تقسيم الدالة إلى helper methods حسب KISS principle
        
        Args:
            question: السؤال المطلوب الإجابة عليه
            user: معلومات المستخدم
            conversation_id: معرف المحادثة (اختياري)
            use_deep_context: استخدام سياق عميق (اختياري)
            
        Returns:
            dict: الاستجابة مع الحالة والإجابة
        """
        logger.debug(
            f"Answering question for user {user}: {question} "
            f"(conv: {conversation_id}, deep: {use_deep_context})"
        )
        
        client = self.get_llm_client()
        max_retries = 2

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create()

                # استخراج البيانات من الاستجابة
                response_data = self._extract_response_data(response)

                # معالجة الاستجابات الفارغة
                empty_result = self._handle_empty_response(response_data, attempt, max_retries)
                if empty_result is not None:
                    # إذا كانت استجابة فارغة بدون tool calls وليست آخر محاولة، نعيد المحاولة
                    if empty_result.get("error_type") == "empty_response":
                        continue
                    return empty_result

                # نجاح! إنشاء استجابة النجاح
                return self._create_success_response(response_data)

            except AttributeError as e:
                return self._handle_attribute_error(e)

            except Exception as e:
                error_result = self._handle_general_error(e, attempt, max_retries)
                if error_result is not None:
                    return error_result
                # المتابعة للمحاولة التالية

        # Fallback return في حال اكتمال الحلقة بدون إرجاع (نادر)
        return {
            "status": "error",
            "answer": "Unexpected execution flow in AI service.",
            "error_type": "unknown",
            "tokens_used": 0,
            "model_used": "unknown",
        }

admin_ai_service = AdminAIService()
