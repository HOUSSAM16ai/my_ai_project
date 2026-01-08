"""مصنع الاستجابات - محسّن لبيئة FastAPI.

يُنشئ هذا المكوّن استجابات JSON موحّدة وبسيطة للتطبيق.
"""

from fastapi.responses import JSONResponse


class ResponseFactory:
    """يوفر توابع ثابتة لبناء استجابات JSON بشكل متسق وواضح."""

    @staticmethod
    def make_json_response(
        data: dict[str, object],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """ينشئ استجابة JSON باستخدام البيانات وحالة HTTP المحددة."""

        normalized_headers = headers or {}
        return JSONResponse(content=data, status_code=status_code, headers=normalized_headers)

    @staticmethod
    def make_error_response(
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: dict[str, object] | None = None,
    ) -> JSONResponse:
        """ينشئ استجابة خطأ واضحة مع تفاصيل اختيارية."""

        data: dict[str, object] = {
            "error": True,
            "message": message,
            "status_code": status_code,
        }
        if error_code:
            data["error_code"] = error_code
        if details:
            data["details"] = details
        return ResponseFactory.make_json_response(data, status_code)

    @staticmethod
    def make_success_response(
        data: dict[str, str | int | bool] | None = None,
        message: str = "Success",
        status_code: int = 200,
    ) -> JSONResponse:
        """ينشئ استجابة نجاح موحدة مع رسالة اختيارية."""

        response_data: dict[str, object] = {"success": True, "message": message}
        if data is not None:
            response_data["data"] = data
        return ResponseFactory.make_json_response(response_data, status_code)
