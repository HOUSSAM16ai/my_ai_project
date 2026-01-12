"""
تبعيات المصادقة والتفويض لمسارات FastAPI.

تفصل هذه الوحدة منطق استخراج الرموز والتحقق من الأدوار عن الموجهات
لضمان إعادة الاستخدام والاختبار السهل مع توثيق عربي موحّد.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings
from app.core.database import get_db
from app.core.domain.user import User
from app.services.auth import AuthService
from app.services.rbac import ADMIN_ROLE, STANDARD_ROLE, RBACService


@dataclass
class CurrentUser:
    """تمثيل المستخدم الحالي مع الأدوار والصلاحيات."""

    user: User
    roles: list[str]
    permissions: set[str]


async def get_auth_service(db=Depends(get_db)) -> AuthService:
    return AuthService(db, get_settings())


def _extract_bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing"
        )
    return header.split(" ", maxsplit=1)[1]


async def get_current_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    token = _extract_bearer_token(request)
    payload = service.verify_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    user = await service.session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    rbac = RBACService(service.session)
    await rbac.ensure_seed()
    roles = await rbac.user_roles(user.id)

    if not roles:
        desired_role = ADMIN_ROLE if user.is_admin else STANDARD_ROLE
        await rbac.assign_role(user, desired_role)
        roles = await rbac.user_roles(user.id)

    permissions = await rbac.user_permissions(user.id)
    return CurrentUser(user=user, roles=roles, permissions=permissions)


def require_roles(*roles: str):
    async def dependency(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(current.roles).intersection(set(roles)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current

    return dependency


def require_permissions(*permissions: str):
    async def dependency(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(permissions).issubset(current.permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing permissions")
        return current

    return dependency


def require_permissions_or_admin(*permissions: str):
    """تبعيات تفويض تمنح استثناءً للمستخدمين الإداريين مع احترام الصلاحيات الصريحة.

    Args:
        *permissions: قائمة الصلاحيات المطلوب تحققها.

    Returns:
        CurrentUser: كائن المستخدم الحالي بعد التحقق من الصلاحيات أو صفة الإداري.

    Raises:
        HTTPException: في حال غياب الصلاحيات المطلوبة لمستخدم غير إداري.
    """

    async def dependency(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.user.is_admin:
            return current

        if not set(permissions).issubset(current.permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing permissions")

        return current

    return dependency


def reauth_dependency():
    async def dependency(
        request: Request,
        current: CurrentUser = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> CurrentUser:
        token = request.headers.get("X-Reauth-Token")
        password = request.headers.get("X-Reauth-Password")
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        if token:
            await auth_service.verify_reauth_proof(
                token,
                user=current.user,
                ip=client_ip,
                user_agent=user_agent,
            )
            return current

        if password and current.user.check_password(password):
            return current

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Re-authentication required"
        )

    return dependency
