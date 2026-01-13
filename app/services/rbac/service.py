"""
خدمة التحكم بالوصول المبني على الأدوار (RBAC Service).

توفر واجهة للتحقق من الصلاحيات وإدارة أدوار المستخدمين،
مفصولة عن منطق التهيئة (Seeding) لتبسيط المسؤوليات.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import Permission, Role, User, UserRole
from app.services.rbac.seeder import RBACSeeder


class RBACService:
    """
    طبقة خدمة لإدارة الأدوار والصلاحيات والتحقق منها.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._seeder = RBACSeeder(session)

    async def ensure_seed(self) -> None:
        """
        تهيئة الأدوار والصلاحيات الافتراضية عند بدء النظام.
        """
        await self._seeder.ensure_seed()

    async def assign_role(self, user: User, role_name: str) -> None:
        """
        إسناد دور للمستخدم مع ضمان عدم التكرار.
        """
        roles_map = await self._load_roles()
        role = roles_map.get(role_name)
        if role is None or role.id is None:
            raise ValueError(f"الدور {role_name} غير موجود")

        link_exists = await self.session.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
        )
        if link_exists.scalar_one_or_none():
            return

        self.session.add(UserRole(user_id=user.id, role_id=role.id))
        await self.session.commit()

    async def user_roles(self, user_id: int) -> list[str]:
        result = await self.session.execute(
            select(Role.name)
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        return [row[0] for row in result.all()]

    async def user_permissions(self, user_id: int) -> set[str]:
        result = await self.session.execute(
            select(Permission.name)
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(UserRole.user_id == user_id)
        )
        return {row[0] for row in result.all()}

    async def require_roles(self, user_id: int, allowed: Iterable[str]) -> None:
        roles = set(await self.user_roles(user_id))
        if not roles.intersection(set(allowed)):
            raise PermissionError("المستخدم يفتقر إلى الدور المطلوب")

    async def require_permissions(self, user_id: int, required: Iterable[str]) -> None:
        perms = await self.user_permissions(user_id)
        missing = set(required) - perms
        if missing:
            raise PermissionError("المستخدم يفتقر إلى الصلاحيات المطلوبة")

    async def _load_roles(self) -> dict[str, Role]:
        result = await self.session.execute(select(Role))
        roles = result.scalars().all()
        return {role.name: role for role in roles if role.id is not None}
