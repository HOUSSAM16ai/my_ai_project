# ======================================================================================
# ==                    BASE VALIDATOR CLASS (v1.0)                                  ==
# ======================================================================================
# PRIME DIRECTIVE:
#   فئة أساسية للتحقق من صحة البيانات - Base validator with enterprise patterns

from typing import Any, ClassVar

from marshmallow import Schema, ValidationError


class BaseValidator:
    """
    فئة أساسية للتحقق من صحة البيانات - Base validator class

    Features:
    - Standardized validation interface
    - Error formatting and handling
    - Schema caching for performance
    """

    _schema_cache: ClassVar[dict[str, Schema]] = {}

    @classmethod
    def validate(
        cls, schema_class: type, data: dict[str, Any], partial: bool = False
    ) -> tuple[bool, dict | None, dict | None]:
        """
        التحقق من صحة البيانات باستخدام schema محدد

        Args:
            schema_class: Marshmallow schema class
            data: البيانات المراد التحقق منها
            partial: السماح بالتحديث الجزئي

        Returns:
            Tuple of (success, validated_data, errors)
        """
        # Get or create schema instance
        schema_key = f"{schema_class.__name__}_{partial}"
        if schema_key not in cls._schema_cache:
            cls._schema_cache[schema_key] = schema_class(partial=partial)

        schema = cls._schema_cache[schema_key]

        try:
            # Validate and deserialize
            validated_data = schema.load(data)
            return True, validated_data, None
        except ValidationError as err:
            # Format errors
            # err.messages can be dict, list, or str - handle appropriately
            messages = err.messages
            invalid_fields = list(messages.keys()) if isinstance(messages, dict) else []

            errors = {
                "validation_errors": messages,
                "invalid_fields": invalid_fields,
            }
            return False, None, errors

    @classmethod
    def format_error_response(
        cls, errors: dict[str, Any], status_code: int = 400
    ) -> tuple[dict, int]:
        """
        تنسيق استجابة خطأ موحدة

        Args:
            errors: أخطاء التحقق
            status_code: رمز حالة HTTP

        Returns:
            Tuple of (response_dict, status_code)
        """
        return {
            "success": False,
            "error": {"code": status_code, "message": "Validation failed", "details": errors},
        }, status_code

    @classmethod
    def format_success_response(
        cls, data: Any, message: str = "Success", metadata: dict | None = None
    ) -> dict:
        """
        تنسيق استجابة نجاح موحدة

        Args:
            data: البيانات المراد إرجاعها
            message: رسالة النجاح
            metadata: بيانات وصفية إضافية

        Returns:
            Formatted response dictionary
        """
        response = {"success": True, "message": message, "data": data}

        if metadata:
            response["metadata"] = metadata

        return response
