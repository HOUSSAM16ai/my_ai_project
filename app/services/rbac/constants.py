"""
ثوابت خدمة التحكم بالوصول (RBAC Constants).

يحتوي هذا الملف على تعريفات الأدوار، الصلاحيات، والبيانات الافتراضية
التي تستخدم لتهيئة النظام وتطبيق السياسات.
"""

from typing import Final

STANDARD_ROLE: Final[str] = "STANDARD_USER"
ADMIN_ROLE: Final[str] = "ADMIN"

USERS_READ: Final[str] = "USERS_READ"
USERS_WRITE: Final[str] = "USERS_WRITE"
ROLES_WRITE: Final[str] = "ROLES_WRITE"
AUDIT_READ: Final[str] = "AUDIT_READ"
AI_CONFIG_READ: Final[str] = "AI_CONFIG_READ"
AI_CONFIG_WRITE: Final[str] = "AI_CONFIG_WRITE"
ACCOUNT_SELF: Final[str] = "ACCOUNT_SELF"
QA_SUBMIT: Final[str] = "QA_SUBMIT"

DEFAULT_ROLE_PERMISSIONS: Final[dict[str, set[str]]] = {
    STANDARD_ROLE: {QA_SUBMIT, ACCOUNT_SELF},
    ADMIN_ROLE: {
        USERS_READ,
        USERS_WRITE,
        ROLES_WRITE,
        AUDIT_READ,
        AI_CONFIG_READ,
        AI_CONFIG_WRITE,
        QA_SUBMIT,
        ACCOUNT_SELF,
    },
}

PERMISSION_DESCRIPTIONS: Final[dict[str, str]] = {
    USERS_READ: "قراءة بيانات المستخدمين",
    USERS_WRITE: "تعديل/إنشاء حسابات المستخدمين",
    ROLES_WRITE: "تعيين وإدارة أدوار المستخدمين بإجراءات كسر الزجاج",
    AUDIT_READ: "قراءة سجلات التدقيق",
    AI_CONFIG_READ: "قراءة إعدادات الذكاء الاصطناعي",
    AI_CONFIG_WRITE: "تعديل إعدادات الذكاء الاصطناعي",
    ACCOUNT_SELF: "إدارة الحساب الشخصي وتحديث كلمة المرور",
    QA_SUBMIT: "إرسال أسئلة تعليمية",
}
