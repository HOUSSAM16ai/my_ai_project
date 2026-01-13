"""
نظام تسخين التخزين المؤقت (Cache Warming).

يسمح هذا النظام بتحميل البيانات المهمة بشكل استباقي في الذاكرة المؤقتة
لضمان أداء عالٍ منذ اللحظة الأولى للتشغيل (Cold Start Mitigation).

المبادئ:
- التسجيل (Registration): يمكن لأي مكون تسجيل دالة "تسخين".
- التزامن (Concurrency): تنفيذ عمليات التسخين بشكل متوازي.
- المرونة (Resilience): فشل عملية تسخين واحدة لا يوقف النظام.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.caching.base import CacheBackend

logger = logging.getLogger(__name__)


@dataclass
class WarmerTask:
    """تعريف مهمة تسخين."""

    name: str
    func: Callable[[], Awaitable[object]] | Callable[[], object]
    priority: int = 10  # الأولوية (الأعلى ينفذ أولاً)
    ttl: int | None = None  # مدة بقاء البيانات (اختياري، يعتمد على المنطق داخل الدالة)


class CacheWarmer:
    """
    محرك تسخين الكاش (Cache Warmer Engine).
    """

    def __init__(self, backend: CacheBackend) -> None:
        self.backend = backend
        self._tasks: dict[str, WarmerTask] = {}

    def register(
        self,
        name: str,
        func: Callable[[], Awaitable[object]] | Callable[[], object],
        priority: int = 10,
        ttl: int | None = None,
    ) -> None:
        """
        تسجيل دالة تسخين جديدة.

        Args:
            name: اسم المهمة (يجب أن يكون فريداً).
            func: الدالة التي ستقوم بجلب البيانات وإرجاعها (أو تخزينها مباشرة).
                  إذا أرجعت قيمة، سيتم تخزينها في الكاش باستخدام الاسم كمفتاح (اختياري).
                  يفضل أن تقوم الدالة بنفسها باستدعاء backend.set إذا كانت البيانات معقدة.
            priority: أولوية التنفيذ (10 = عادي، 1 = عالي).
            ttl: TTL اختياري.
        """
        self._tasks[name] = WarmerTask(name, func, priority, ttl)
        logger.debug(f"🔥 Registered cache warmer task: {name}")

    async def warm_up(self, specific_tasks: list[str] | None = None) -> dict[str, bool]:
        """
        تنفيذ عملية التسخين.

        Args:
            specific_tasks: قائمة بأسماء المهام لتنفيذها فقط (اختياري).

        Returns:
            dict[str, bool]: نتيجة كل مهمة (True = نجاح).
        """
        tasks_to_run = []
        if specific_tasks:
            for name in specific_tasks:
                if name in self._tasks:
                    tasks_to_run.append(self._tasks[name])
        else:
            tasks_to_run = list(self._tasks.values())

        # ترتيب حسب الأولوية (الأقل رقماً أولاً)
        tasks_to_run.sort(key=lambda t: t.priority)

        logger.info(f"🔥 Starting cache warm-up for {len(tasks_to_run)} tasks...")
        start_time = time.time()

        results: dict[str, bool] = {}

        # يمكننا تنفيذ المهام بشكل متزامن (Concurrency) لتقليل وقت البدء
        # نستخدم return_exceptions=True لضمان عدم توقف العملية عند فشل مهمة
        coroutines = [self._execute_task(task) for task in tasks_to_run]

        if not coroutines:
            return {}

        outcomes = await asyncio.gather(*coroutines, return_exceptions=True)

        for task, outcome in zip(tasks_to_run, outcomes, strict=False):
            if isinstance(outcome, Exception):
                logger.error(f"❌ Warmer task '{task.name}' failed: {outcome}")
                results[task.name] = False
            else:
                results[task.name] = True

        duration = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        logger.info(
            f"✅ Cache warm-up completed in {duration:.2f}s. "
            f"Success: {success_count}/{len(tasks_to_run)}"
        )
        return results

    async def _execute_task(self, task: WarmerTask) -> None:
        """تنفيذ مهمة واحدة."""
        logger.debug(f"▶️ Executing warmer: {task.name}")

        # دعم الدوال المتزامنة وغير المتزامنة
        import inspect

        if inspect.iscoroutinefunction(task.func):
            result = await task.func()  # type: ignore
        else:
            result = task.func()  # type: ignore

        # إذا أرجعت الدالة قيمة (وليست None)، نفترض أنها تريد تخزينها تحت اسم المهمة
        if result is not None:
            # هنا نفترض أن اسم المهمة هو المفتاح، وهذا نمط بسيط.
            # الأفضل عادة أن تقوم الدالة بنفسها بالتخزين داخل الكاش إذا كانت مفاتيح متعددة.
            await self.backend.set(task.name, result, ttl=task.ttl)
