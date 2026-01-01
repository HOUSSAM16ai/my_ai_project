"""
استراتيجية إعادة المحاولة للأخطاء العابرة.
Retry strategy for transient errors.
"""

import openai

class RetryStrategy:
    """
    يحدد ما إذا كان الخطأ قابلاً لإعادة المحاولة ويصنف الأخطاء.
    Determines if an error is retryable and classifies errors.
    """

    @staticmethod
    def classify_error(exc: Exception) -> str:
        """
        يصنف الخطأ إلى فئة معروفة.
        Classifies the error into a known category.
        """
        if isinstance(exc, openai.RateLimitError):
            return "rate_limit"
        if isinstance(exc, openai.APIConnectionError):
            return "connection"
        if isinstance(exc, openai.InternalServerError):
            return "server_error"
        if isinstance(exc, openai.AuthenticationError):
            return "auth"
        if isinstance(exc, openai.BadRequestError):
            return "bad_request" # Usually not retryable
        return "unknown"

    @staticmethod
    def is_retry_allowed(kind: str) -> bool:
        """
        يحدد ما إذا كان النوع قابلاً لإعادة المحاولة.
        Determines if the kind is retryable.
        """
        return kind in {"rate_limit", "connection", "server_error", "unknown"}
