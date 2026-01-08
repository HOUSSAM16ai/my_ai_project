# app/middleware/security/jwt_auth_middleware.py
"""
وسيط المصادقة المركزية عبر JWT.

يطبق هذا الوسيط مبدأ "لا شيء يعمل بدون توكن" مع استثناءات محدودة
لنقاط الدخول العامة (مثل تسجيل الدخول/التسجيل وفحوصات الصحة).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings
from app.core.database import async_session_factory
from app.core.domain.models import User
from app.middleware.core.base_middleware import ConditionalMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.services.auth_service import AuthService
from app.services.rbac import ADMIN_ROLE, STANDARD_ROLE, RBACService


@dataclass(frozen=True)
class AccessPolicy:
    """
    سياسة وصول مرتبطة بمسار محدد.
    """

    path_prefix: str
    required_roles: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


class JwtAuthMiddleware(ConditionalMiddleware):
    """
    وسيط مصادقة مركزي يعتمد على رموز JWT.

    يحول المصادقة إلى طبقة موحدة على مستوى التطبيق ويضيف بيانات المستخدم
    إلى سياق الطلب مع دعم سياسات الوصول المستندة إلى الأدوار والصلاحيات.
    """

    name = "JwtAuth"
    order = 35

    def _setup(self) -> None:
        """تهيئة إعدادات الوسيط وسياسات الوصول."""
        self.settings: AppSettings = self.config["settings"]
        self.policies: list[AccessPolicy] = self.config.get("policies", [])
        self.authenticated_count = 0
        self.denied_count = 0

    async def process_request_async(self, ctx: RequestContext) -> MiddlewareResult:
        """
        يتحقق من صحة التوكن ويُنشئ سياق هوية موحد.
        """
        token = self._extract_token(ctx)
        if not token:
            self.denied_count += 1
            return MiddlewareResult.unauthorized(message="Authentication token required")

        async with async_session_factory() as session:
            auth_service = AuthService(session, self.settings)
            try:
                payload = self._verify_token(auth_service, token)
                subject = payload.get("sub")
                if subject is None:
                    self.denied_count += 1
                    return MiddlewareResult.unauthorized(message="Invalid token payload")

                user_id, user = await self._resolve_user(session, subject)
            except HTTPException:
                self.denied_count += 1
                return MiddlewareResult.unauthorized(message="Invalid token")

            roles, permissions = await self._resolve_access(session, user)
            if not self._policy_allows(ctx, roles, permissions):
                self.denied_count += 1
                return MiddlewareResult.forbidden(message="Access denied by policy")

            ctx.set_user_context(user_id=user_id)
            ctx.add_metadata("user_roles", roles)
            ctx.add_metadata("user_permissions", list(permissions))
            self._propagate_request_state(ctx, user_id, roles, permissions)
            self.authenticated_count += 1
            return MiddlewareResult.success()

    def _extract_token(self, ctx: RequestContext) -> str | None:
        """
        استخراج التوكن من الترويسات القياسية أو خدمة-إلى-خدمة.
        """
        auth_header = ctx.get_header("Authorization")
        if auth_header.lower().startswith("bearer "):
            return auth_header.split(" ", maxsplit=1)[1].strip()

        service_token = ctx.get_header("X-Service-Token")
        return service_token.strip() if service_token else None

    def _verify_token(self, auth_service: AuthService, token: str) -> dict[str, object]:
        """
        التحقق من صحة التوكن باستخدام خدمة المصادقة.
        """
        try:
            return auth_service.verify_access_token(token)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    async def _resolve_user(self, session: AsyncSession, subject: object) -> tuple[str, User | None]:
        """
        جلب المستخدم المقابل للمعرّف في التوكن مع دعم الهويات الخدمية.
        """
        user_id = str(subject)
        try:
            numeric_id = int(user_id)
        except (TypeError, ValueError):
            return user_id, None

        user = await session.get(User, numeric_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user_id, user

    async def _resolve_access(
        self,
        session: AsyncSession,
        user: User | None,
    ) -> tuple[list[str], set[str]]:
        """
        استخراج الأدوار والصلاحيات للمستخدم أو إرجاع قيم افتراضية للخدمات.
        """
        if user is None:
            return ["service"], set()

        rbac = RBACService(session)
        await rbac.ensure_seed()
        roles = await rbac.user_roles(user.id)
        if not roles:
            desired_role = ADMIN_ROLE if user.is_admin else STANDARD_ROLE
            await rbac.assign_role(user, desired_role)
            roles = await rbac.user_roles(user.id)
        permissions = await rbac.user_permissions(user.id)
        return roles, permissions

    def _policy_allows(self, ctx: RequestContext, roles: list[str], permissions: set[str]) -> bool:
        """
        التحقق من سياسات الوصول المحددة مسبقًا.
        """
        for policy in self.policies:
            if not ctx.path.startswith(policy.path_prefix):
                continue
            if policy.methods and ctx.method not in policy.methods:
                continue
            if policy.required_roles and not set(policy.required_roles).intersection(set(roles)):
                return False
            if policy.required_permissions and not set(policy.required_permissions).issubset(permissions):
                return False
        return True

    def _propagate_request_state(
        self,
        ctx: RequestContext,
        user_id: str,
        roles: list[str],
        permissions: set[str],
    ) -> None:
        """
        حفظ بيانات المستخدم على كائن الطلب الأصلي لتكامل أفضل.
        """
        request = ctx._raw_request
        if request is None:
            return
        request.state.user_id = user_id
        request.state.user_roles = roles
        request.state.user_permissions = list(permissions)

    def get_statistics(self) -> dict[str, object]:
        """إرجاع إحصاءات المصادقة لهذا الوسيط."""
        stats = super().get_statistics()
        stats.update(
            {
                "authenticated_count": self.authenticated_count,
                "denied_count": self.denied_count,
            }
        )
        return stats
