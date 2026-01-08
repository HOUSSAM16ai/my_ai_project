"""
نظام التحكم بالوصول القائم على الأدوار (Role-Based Access Control).

يوفر نظام RBAC كامل مع دعم الأدوار والصلاحيات الديناميكية.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Permission(Enum):
    """الصلاحيات المتاحة في النظام."""
    
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Plan permissions
    PLAN_READ = "plan:read"
    PLAN_WRITE = "plan:write"
    PLAN_DELETE = "plan:delete"
    
    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_MANAGE = "system:manage"


@dataclass(frozen=True, slots=True)
class Role:
    """
    دور في النظام.
    
    Attributes:
        name: اسم الدور
        permissions: الصلاحيات المرتبطة
        description: وصف الدور
    """
    
    name: str
    permissions: frozenset[Permission]
    description: str = ""


# الأدوار المعرفة مسبقاً
PREDEFINED_ROLES: dict[str, Role] = {
    "admin": Role(
        name="admin",
        permissions=frozenset(Permission),  # جميع الصلاحيات
        description="مدير النظام - صلاحيات كاملة",
    ),
    "user": Role(
        name="user",
        permissions=frozenset([
            Permission.USER_READ,
            Permission.PLAN_READ,
            Permission.PLAN_WRITE,
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
        ]),
        description="مستخدم عادي - صلاحيات محدودة",
    ),
    "viewer": Role(
        name="viewer",
        permissions=frozenset([
            Permission.USER_READ,
            Permission.PLAN_READ,
            Permission.MEMORY_READ,
        ]),
        description="مشاهد - قراءة فقط",
    ),
    "moderator": Role(
        name="moderator",
        permissions=frozenset([
            Permission.USER_READ,
            Permission.USER_WRITE,
            Permission.PLAN_READ,
            Permission.PLAN_WRITE,
            Permission.PLAN_DELETE,
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
            Permission.SYSTEM_MONITOR,
        ]),
        description="مشرف - صلاحيات إدارية محدودة",
    ),
}


@dataclass(slots=True)
class UserRoles:
    """
    أدوار المستخدم.
    
    Attributes:
        user_id: معرف المستخدم
        roles: الأدوار المعينة
        custom_permissions: صلاحيات مخصصة إضافية
    """
    
    user_id: str
    roles: set[str] = field(default_factory=set)
    custom_permissions: set[Permission] = field(default_factory=set)


class RBACManager:
    """
    مدير التحكم بالوصول القائم على الأدوار.
    
    الميزات:
    - إدارة الأدوار
    - إدارة الصلاحيات
    - تعيين الأدوار للمستخدمين
    - التحقق من الصلاحيات
    - أدوار مخصصة
    
    المبادئ:
    - Principle of Least Privilege: أقل صلاحيات ممكنة
    - Separation of Duties: فصل المسؤوليات
    - Dynamic: دعم الأدوار الديناميكية
    - Auditable: تسجيل جميع العمليات
    """
    
    def __init__(self) -> None:
        """تهيئة مدير RBAC."""
        self._roles: dict[str, Role] = PREDEFINED_ROLES.copy()
        self._user_roles: dict[str, UserRoles] = {}
        
        logger.info("✅ RBAC Manager initialized")
    
    def create_role(
        self,
        name: str,
        permissions: set[Permission],
        description: str = "",
    ) -> Role:
        """
        ينشئ دوراً جديداً.
        
        Args:
            name: اسم الدور
            permissions: الصلاحيات
            description: وصف الدور
            
        Returns:
            Role: الدور المُنشأ
        """
        role = Role(
            name=name,
            permissions=frozenset(permissions),
            description=description,
        )
        
        self._roles[name] = role
        
        logger.info(f"✅ Role created: {name}")
        
        return role
    
    def delete_role(self, name: str) -> bool:
        """
        يحذف دوراً.
        
        Args:
            name: اسم الدور
            
        Returns:
            bool: True إذا تم الحذف
        """
        if name in PREDEFINED_ROLES:
            logger.warning(f"⚠️ Cannot delete predefined role: {name}")
            return False
        
        if name in self._roles:
            del self._roles[name]
            logger.info(f"✅ Role deleted: {name}")
            return True
        
        return False
    
    def get_role(self, name: str) -> Role | None:
        """
        يحصل على دور.
        
        Args:
            name: اسم الدور
            
        Returns:
            Role | None: الدور أو None
        """
        return self._roles.get(name)
    
    def list_roles(self) -> list[Role]:
        """
        يعرض جميع الأدوار.
        
        Returns:
            list[Role]: قائمة الأدوار
        """
        return list(self._roles.values())
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """
        يعين دوراً لمستخدم.
        
        Args:
            user_id: معرف المستخدم
            role_name: اسم الدور
            
        Returns:
            bool: True إذا تم التعيين
        """
        if role_name not in self._roles:
            logger.warning(f"⚠️ Role not found: {role_name}")
            return False
        
        if user_id not in self._user_roles:
            self._user_roles[user_id] = UserRoles(user_id=user_id)
        
        self._user_roles[user_id].roles.add(role_name)
        
        logger.info(f"✅ Role '{role_name}' assigned to user: {user_id}")
        
        return True
    
    def revoke_role(self, user_id: str, role_name: str) -> bool:
        """
        يلغي دوراً من مستخدم.
        
        Args:
            user_id: معرف المستخدم
            role_name: اسم الدور
            
        Returns:
            bool: True إذا تم الإلغاء
        """
        if user_id not in self._user_roles:
            return False
        
        if role_name in self._user_roles[user_id].roles:
            self._user_roles[user_id].roles.remove(role_name)
            logger.info(f"✅ Role '{role_name}' revoked from user: {user_id}")
            return True
        
        return False
    
    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        """
        يمنح صلاحية مخصصة لمستخدم.
        
        Args:
            user_id: معرف المستخدم
            permission: الصلاحية
            
        Returns:
            bool: True إذا تم المنح
        """
        if user_id not in self._user_roles:
            self._user_roles[user_id] = UserRoles(user_id=user_id)
        
        self._user_roles[user_id].custom_permissions.add(permission)
        
        logger.info(f"✅ Permission '{permission.value}' granted to user: {user_id}")
        
        return True
    
    def revoke_permission(self, user_id: str, permission: Permission) -> bool:
        """
        يلغي صلاحية مخصصة من مستخدم.
        
        Args:
            user_id: معرف المستخدم
            permission: الصلاحية
            
        Returns:
            bool: True إذا تم الإلغاء
        """
        if user_id not in self._user_roles:
            return False
        
        if permission in self._user_roles[user_id].custom_permissions:
            self._user_roles[user_id].custom_permissions.remove(permission)
            logger.info(f"✅ Permission '{permission.value}' revoked from user: {user_id}")
            return True
        
        return False
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        يتحقق من وجود صلاحية لمستخدم.
        
        Args:
            user_id: معرف المستخدم
            permission: الصلاحية المطلوبة
            
        Returns:
            bool: True إذا كانت الصلاحية موجودة
        """
        if user_id not in self._user_roles:
            return False
        
        user_roles = self._user_roles[user_id]
        
        # التحقق من الصلاحيات المخصصة
        if permission in user_roles.custom_permissions:
            return True
        
        # التحقق من صلاحيات الأدوار
        for role_name in user_roles.roles:
            role = self._roles.get(role_name)
            if role and permission in role.permissions:
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> set[Permission]:
        """
        يحصل على جميع صلاحيات مستخدم.
        
        Args:
            user_id: معرف المستخدم
            
        Returns:
            set[Permission]: مجموعة الصلاحيات
        """
        if user_id not in self._user_roles:
            return set()
        
        user_roles = self._user_roles[user_id]
        permissions = set(user_roles.custom_permissions)
        
        # إضافة صلاحيات الأدوار
        for role_name in user_roles.roles:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        
        return permissions
    
    def get_user_roles(self, user_id: str) -> list[str]:
        """
        يحصل على أدوار مستخدم.
        
        Args:
            user_id: معرف المستخدم
            
        Returns:
            list[str]: قائمة الأدوار
        """
        if user_id not in self._user_roles:
            return []
        
        return list(self._user_roles[user_id].roles)
    
    def get_stats(self) -> dict[str, Any]:
        """
        يحصل على إحصائيات RBAC.
        
        Returns:
            dict[str, Any]: إحصائيات مفصلة
        """
        return {
            "total_roles": len(self._roles),
            "predefined_roles": len(PREDEFINED_ROLES),
            "custom_roles": len(self._roles) - len(PREDEFINED_ROLES),
            "total_users": len(self._user_roles),
            "roles": {
                name: {
                    "permissions_count": len(role.permissions),
                    "description": role.description,
                }
                for name, role in self._roles.items()
            },
        }


# مثيل عام
_global_rbac_manager: RBACManager | None = None


def get_rbac_manager() -> RBACManager:
    """
    يحصل على مدير RBAC العام.
    
    Returns:
        RBACManager: مدير RBAC
    """
    global _global_rbac_manager
    if _global_rbac_manager is None:
        _global_rbac_manager = RBACManager()
    return _global_rbac_manager
