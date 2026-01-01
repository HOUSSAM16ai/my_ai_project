"""Policy Governance - Data governance and access control."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class DataClassification(Enum):
    """تصنيف البيانات"""
    PUBLIC = 'public'
    INTERNAL = 'internal'
    CONFIDENTIAL = 'confidential'
    HIGHLY_RESTRICTED = 'highly_restricted'

@dataclass
class DataGovernancePolicy:
    """سياسة حوكمة البيانات"""
    classification: DataClassification
    retention_days: int
    encryption_required: bool
    backup_required: bool
    access_logging_required: bool
    allowed_locations: list[str]

class DataGovernanceFramework:
    """
    إطار حوكمة البيانات (Data Governance Framework)

    يدير سياسات البيانات بشكل موحد:
    - تصنيف البيانات
    - سياسات الاحتفاظ
    - سياسات التشفير
    - سياسات الوصول
    """

    def __init__(self):
        self.policies: dict[DataClassification, DataGovernancePolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) ->None:
        """تهيئة السياسات الافتراضية"""
        self.policies[DataClassification.PUBLIC] = DataGovernancePolicy(
            classification=DataClassification.PUBLIC, retention_days=365,
            encryption_required=False, backup_required=True,
            access_logging_required=False, allowed_locations=['*'])
        self.policies[DataClassification.INTERNAL] = DataGovernancePolicy(
            classification=DataClassification.INTERNAL, retention_days=730,
            encryption_required=True, backup_required=True,
            access_logging_required=True, allowed_locations=['*'])
        self.policies[DataClassification.CONFIDENTIAL] = DataGovernancePolicy(
            classification=DataClassification.CONFIDENTIAL, retention_days=
            2190, encryption_required=True, backup_required=True,
            access_logging_required=True, allowed_locations=['EU', 'US'])
        self.policies[DataClassification.HIGHLY_RESTRICTED
            ] = DataGovernancePolicy(classification=DataClassification.
            HIGHLY_RESTRICTED, retention_days=2555, encryption_required=
            True, backup_required=True, access_logging_required=True,
            allowed_locations=['EU'])

    def get_policy(self, classification: DataClassification
        ) ->DataGovernancePolicy:
        """الحصول على سياسة لتصنيف معين"""
        return self.policies[classification]

    def should_encrypt(self, classification: DataClassification) ->bool:
        """التحقق مما إذا كان التشفير مطلوب"""
        return self.policies[classification].encryption_required

    def is_location_allowed(self, classification: DataClassification,
        location: str) ->bool:
        """التحقق مما إذا كان الموقع مسموح"""
        allowed = self.policies[classification].allowed_locations
        return '*' in allowed or location in allowed
