# app/middleware/core/pipeline.py
# ======================================================================================
# ==                    SMART MIDDLEWARE PIPELINE (v∞)                              ==
# ======================================================================================
"""خط أنابيب ذكي ينسق الوسطاء بوضوح وتعقب دقيق."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .base_middleware import BaseMiddleware
from .context import RequestContext
from .result import MiddlewareResult


@dataclass
class MiddlewareStatistics:
    """يجمع مؤشرات تشغيل وسيط واحد مع حساب المتوسط تلقائياً."""

    executions: int = 0
    successes: int = 0
    failures: int = 0
    total_time: float = 0.0

    @property
    def average_time(self) -> float:
        """يحسب متوسط زمن التنفيذ بالثواني مع حماية من القسمة على صفر."""

        return self.total_time / self.executions if self.executions else 0.0

    def register(self, success: bool, duration: float) -> None:
        """يحدّث العدادات بعد تشغيل الوسيط مرة واحدة."""

        self.executions += 1
        self.total_time += duration
        if success:
            self.successes += 1
            return
        self.failures += 1


@dataclass
class PipelineStatistics:
    """يحفظ لقطات الأداء العامة وخريطة إحصاءات كل وسيط."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time: float = 0.0
    middleware_stats: dict[str, MiddlewareStatistics] = field(default_factory=dict)

    def snapshot(self) -> dict[str, object]:
        """يعيد قاموساً مبسطاً يصلح للقياس والعرض."""

        total_requests = self.total_requests
        middleware_stats = {
            name: {
                "executions": stats.executions,
                "successes": stats.successes,
                "failures": stats.failures,
                "total_time": stats.total_time,
                "average_time": stats.average_time,
            }
            for name, stats in self.middleware_stats.items()
        }

        average_execution_time = (
            self.total_execution_time / total_requests if total_requests else 0.0
        )
        success_rate = (
            self.successful_requests / total_requests if total_requests else 0.0
        )

        return {
            "total_requests": total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": average_execution_time,
            "middleware_count": len(self.middleware_stats),
            "middleware_stats": middleware_stats,
        }


class SmartPipeline:
    """يدير الوسطاء بترتيب مضبوط مع اختصار ذكي وإحصاءات مفهومة."""

    def __init__(self, middlewares: list[BaseMiddleware] | None = None):
        """يهيئ خط الأنابيب مع تهيئة الإحصاءات وترتيب الوسطاء المدخلين."""

        self.middlewares: list[BaseMiddleware] = []
        self._execution_stats = PipelineStatistics()

        if middlewares:
            for middleware in middlewares:
                self.add_middleware(middleware)

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """يضيف وسيطاً جديداً ويرتّب القائمة ويجهّز عداداته."""

        self.middlewares.append(middleware)
        self.middlewares.sort(key=lambda middleware_instance: middleware_instance.order)
        self._execution_stats.middleware_stats.setdefault(
            middleware.name, MiddlewareStatistics()
        )

    def remove_middleware(self, name: str) -> bool:
        """يزيل الوسيط المحدد وينظف إحصاءاته إن وُجدت."""

        for index, middleware in enumerate(self.middlewares):
            if middleware.name == name:
                self.middlewares.pop(index)
                self._execution_stats.middleware_stats.pop(name, None)
                return True
        return False

    def _execute_middleware(
        self,
        middleware: BaseMiddleware,
        ctx: RequestContext,
        process_func: Callable[[RequestContext], MiddlewareResult],
    ) -> MiddlewareResult | None:
        """يشغّل وسيطاً واحداً مع حصر المدة والتعامل الآمن مع الأخطاء."""

        start = time.perf_counter()
        try:
            result = process_func(ctx)
            self._register_middleware_result(
                middleware, ctx, result, time.perf_counter() - start
            )
            return result if not result.should_continue else None
        except Exception as exc:  # pragma: no cover - مسار حراسة
            failure = MiddlewareResult.internal_error(
                f"Middleware {middleware.name} failed: {exc!s}"
            )
            self._register_middleware_result(
                middleware, ctx, failure, time.perf_counter() - start, exc
            )
            return failure

    def run(self, ctx: RequestContext) -> MiddlewareResult:
        """ينفذ الوسطاء بشكل متزامن مع دعم الاختصار عند أول فشل."""

        start_time = time.perf_counter()
        self._execution_stats.total_requests += 1
        final_result = MiddlewareResult.success()

        for middleware in self.middlewares:
            if not middleware.should_process(ctx):
                continue

            result = self._execute_middleware(middleware, ctx, middleware.process_request)
            if result:
                final_result = result
                if not result.is_success:
                    self._execution_stats.failed_requests += 1
                break

        total_time = time.perf_counter() - start_time
        self._execution_stats.total_execution_time += total_time
        if final_result.is_success:
            self._execution_stats.successful_requests += 1

        return final_result

    async def run_async(self, ctx: RequestContext) -> MiddlewareResult:
        """ينفذ الوسطاء بشكل غير متزامن بنفس منطق الاختصار والتسجيل."""

        start_time = time.perf_counter()
        self._execution_stats.total_requests += 1
        final_result = MiddlewareResult.success()

        for middleware in self.middlewares:
            if not middleware.should_process(ctx):
                continue

            result = await self._execute_middleware_async(
                middleware, ctx, middleware.process_request_async
            )
            if result:
                final_result = result
                if not result.is_success:
                    self._execution_stats.failed_requests += 1
                break

        total_time = time.perf_counter() - start_time
        self._execution_stats.total_execution_time += total_time
        if final_result.is_success:
            self._execution_stats.successful_requests += 1

        return final_result

    async def _execute_middleware_async(
        self,
        mw: BaseMiddleware,
        ctx: RequestContext,
        process_func: Callable[[RequestContext], Awaitable[MiddlewareResult]],
    ) -> MiddlewareResult | None:
        """يشغّل وسيطاً واحداً بشكل غير متزامن مع الحراسة من الأعطال."""

        start = time.perf_counter()
        try:
            result = await process_func(ctx)
            self._register_middleware_result(
                mw, ctx, result, time.perf_counter() - start
            )
            return result if not result.should_continue else None
        except Exception as exc:  # pragma: no cover - مسار حراسة
            failure = MiddlewareResult.internal_error(
                f"Middleware {mw.name} failed: {exc!s}"
            )
            self._register_middleware_result(
                mw, ctx, failure, time.perf_counter() - start, exc
            )
            return failure

    def _register_middleware_result(
        self,
        middleware: BaseMiddleware,
        ctx: RequestContext,
        result: MiddlewareResult,
        duration: float,
        error: Exception | None = None,
    ) -> None:
        """يحدّث إحصاءات الوسيط ويستدعي الخطافات المناسبة."""

        stats = self._execution_stats.middleware_stats.get(middleware.name)
        if stats is None:
            stats = MiddlewareStatistics()
            self._execution_stats.middleware_stats[middleware.name] = stats

        stats.register(result.is_success, duration)

        if result.is_success:
            middleware.on_success(ctx)
        else:
            middleware.on_error(ctx, error or Exception(result.message))
        middleware.on_complete(ctx, result)

    def get_statistics(self) -> dict[str, object]:
        """يعيد ملخص الإحصاءات الحالي للخط بالكامل."""

        return self._execution_stats.snapshot()

    def reset_statistics(self) -> None:
        """يعيد تعيين العدادات مع الحفاظ على الوسطاء المسجلين."""

        self._execution_stats = PipelineStatistics(
            middleware_stats={
                middleware.name: MiddlewareStatistics()
                for middleware in self.middlewares
            }
        )

    def get_middleware_list(self) -> list[str]:
        """يعيد قائمة مرتبة بأسماء الوسطاء المسجلين."""

        return [middleware.name for middleware in self.middlewares]

    def __repr__(self) -> str:
        """يعطي تمثيلاً نصياً مختصراً لخط الأنابيب."""

        return f"SmartPipeline(middlewares={len(self.middlewares)})"
