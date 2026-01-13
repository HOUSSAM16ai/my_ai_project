"""
منطق تهيئة الأدوار والصلاحيات (RBAC Seeder).

تُعنى هذه الوحدة بإنشاء وتحديث البيانات الأساسية للأدوار والصلاحيات
في قاعدة البيانات، مما يضمن حالة متسقة للنظام عند البدء.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.common import utc_now
from app.core.domain.user import Permission, Role, RolePermission
from app.services.rbac.constants import (
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_DESCRIPTIONS,
)


class RBACSeeder:
    """
    فئة مسؤولة عن بذر وتزامن بيانات RBAC الأولية.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_seed(self) -> None:
        """
        تهيئة الأدوار والصلاحيات الافتراضية عند بدء النظام.
        """
        await self._seed_permissions()
        await self._seed_roles()

    async def _seed_permissions(self) -> None:
        existing = await self.session.execute(select(Permission))
        existing_names = {perm.name for perm in existing.scalars().all()}
        missing = set(PERMISSION_DESCRIPTIONS.keys()) - existing_names
        if not missing:
            return

        for name in sorted(missing):
            self.session.add(Permission(name=name, description=PERMISSION_DESCRIPTIONS.get(name)))
        await self.session.commit()

    async def _seed_roles(self) -> None:
        existing = await self.session.execute(select(Role))
        existing_names = {role.name for role in existing.scalars().all()}
        missing_roles = set(DEFAULT_ROLE_PERMISSIONS.keys()) - existing_names
        if not missing_roles:
            await self._sync_role_permissions()
            return

        for role_name in sorted(missing_roles):
            self.session.add(Role(name=role_name, description=f"دور {role_name}"))
        await self.session.commit()
        await self._sync_role_permissions()

    async def _sync_role_permissions(self) -> None:
        perms_map = await self._load_permissions()
        roles_map = await self._load_roles()

        for role_name, perm_names in DEFAULT_ROLE_PERMISSIONS.items():
            role = roles_map.get(role_name)
            if not role:
                continue
            desired_ids = {perms_map[name].id for name in perm_names if name in perms_map}
            await self._reconcile_role_permissions(role.id, desired_ids)

    async def _reconcile_role_permissions(
        self, role_id: int, desired_permission_ids: set[int]
    ) -> None:
        existing_links = await self.session.execute(
            select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        )
        existing_ids = {row[0] for row in existing_links.all() if row[0] is not None}
        to_remove = existing_ids - desired_permission_ids
        to_add = desired_permission_ids - existing_ids

        if to_remove:
            await self.session.execute(
                delete(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id.in_(to_remove),
                )
            )
        for perm_id in sorted(to_add):
            self.session.add(
                RolePermission(role_id=role_id, permission_id=perm_id, created_at=utc_now())
            )
        await self.session.commit()

    async def _load_permissions(self) -> dict[str, Permission]:
        result = await self.session.execute(select(Permission))
        perms = result.scalars().all()
        return {perm.name: perm for perm in perms if perm.id is not None}

    async def _load_roles(self) -> dict[str, Role]:
        result = await self.session.execute(select(Role))
        roles = result.scalars().all()
        return {role.name: role for role in roles if role.id is not None}
