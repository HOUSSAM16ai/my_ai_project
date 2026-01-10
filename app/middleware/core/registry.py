"""
سجل الوسيط - Middleware Registry

نظام تسجيل ديناميكي يتيح اكتشاف وربط الوسطاء في وقت التشغيل مع دعم بيانات
تعريفية منظمة. يعتمد على مبدأ «السجل» لضمان مركزية إدارة الوسطاء وإعادة
استخدامهم بكفاءة.
"""

from starlette.types import ASGIApp

from .base_middleware import BaseMiddleware

Metadata = dict[str, object]


class MiddlewareRegistry:
    """إدارة عالمية للوسطاء مع توثيق عربي موجز ومهني."""

    def __init__(self) -> None:
        """يهيئ سجلاً فارغاً للوسطاء مع مخزن للحالات والبيانات التعريفية."""

        self._registry: dict[str, type[BaseMiddleware]] = {}
        self._instances: dict[str, BaseMiddleware] = {}
        self._metadata: dict[str, Metadata] = {}

    def register(
        self,
        name: str,
        middleware_class: type[BaseMiddleware],
        metadata: Metadata | None = None,
    ) -> None:
        """يسجل وسيطاً جديداً ويمنع التكرار لضمان تناسق التكوين."""

        if name in self._registry:
            raise ValueError(f"Middleware '{name}' is already registered")

        self._registry[name] = middleware_class
        self._metadata[name] = metadata or {}

    def unregister(self, name: str) -> bool:
        """يحذف الوسيط المسجل ويزيل حالته وبياناته التعريفية إن وجدت."""

        if name not in self._registry:
            return False

        del self._registry[name]
        self._instances.pop(name, None)
        self._metadata.pop(name, None)
        return True

    def create_instance(
        self,
        name: str,
        app: ASGIApp,
        config: dict[str, object] | None = None,
        cache: bool = True,
    ) -> BaseMiddleware | None:
        """ينشئ مثيلاً للوسيط أو يعيده من الذاكرة المؤقتة عند التفعيل."""

        if cache and name in self._instances:
            return self._instances[name]

        middleware_class = self._registry.get(name)
        if middleware_class is None:
            return None

        instance = middleware_class(app, config=config)
        if cache:
            self._instances[name] = instance

        return instance

    def get_instance(self, name: str) -> BaseMiddleware | None:
        """يعيد مثيل الوسيط المخزن أو `None` إذا لم يوجد."""

        return self._instances.get(name)

    def get_metadata(self, name: str) -> Metadata:
        """يسترجع البيانات التعريفية للوسيط بشكل آمن دون استثناءات."""

        return self._metadata.get(name, {})

    def clear(self) -> None:
        """يفرغ السجل بالكامل بما يشمل الحالات والبيانات التعريفية."""

        self._registry.clear()
        self._instances.clear()
        self._metadata.clear()

    def __contains__(self, name: str) -> bool:
        """يسمح بالتحقق السريع من تسجيل وسيط معين."""

        return name in self._registry

    def __len__(self) -> int:
        """يعيد عدد الوسطاء المسجلين حالياً."""

        return len(self._registry)


_global_registry = MiddlewareRegistry()


def register_middleware(
    name: str, middleware_class: type[BaseMiddleware], metadata: Metadata | None = None
) -> None:
    """واجهة سهلة لتسجيل وسيط على السجل العالمي."""

    _global_registry.register(name, middleware_class, metadata)


def create_middleware(
    name: str, app: ASGIApp, config: dict[str, object] | None = None
) -> BaseMiddleware | None:
    """ينشئ وسيطاً من السجل العالمي مع دعم التكوين والذاكرة المؤقتة."""

    return _global_registry.create_instance(name, app, config)
