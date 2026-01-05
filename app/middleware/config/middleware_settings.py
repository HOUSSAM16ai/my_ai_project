# app/middleware/config/middleware_settings.py
# ======================================================================================
# ==                    MIDDLEWARE SETTINGS (v∞)                                    ==
# ======================================================================================
"""
إعدادات الوسيط - Middleware Settings
====================================

حاوية مضبوطة لتهيئة نظام الوسطاء مع توثيق عربي مبسّط للمطورين الجدد.

توفّر هذه الوحدة واجهةً صريحة لقراءة وكتابة الإعدادات بدون اللجوء إلى
`Any`، مع دعم القيم الأولية والقوائم والقواميس المتداخلة الشائعة في ملفات
التهيئة.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

ConfigPrimitive = str | int | float | bool
"""قيمة أولية مسموح بها في الإعدادات."""

ConfigValue = ConfigPrimitive | list[ConfigPrimitive] | dict[str, ConfigPrimitive | list[ConfigPrimitive]]
"""قيمة إعداد مركّبة تدعم القوائم والقواميس المتداخلة البسيطة."""


@dataclass(slots=True)
class MiddlewareSettings:
    """واجهة موحّدة لإدارة إعدادات الوسطاء.

    تعتمد الحاوية على قاموس داخلي ثابت الأنواع، وتقدّم عمليات قراءة وكتابة
    بسيطة مع نسخ دفاعي حتى لا يتأثر المستهلكون بتغييرات داخلية غير مقصودة.
    """

    _config: dict[str, ConfigValue] = field(default_factory=dict)

    @classmethod
    def from_items(cls, items: Iterable[tuple[str, ConfigValue]]) -> "MiddlewareSettings":
        """ينشئ إعدادات من أزواج مفاتيح وقيم.

        يسهّل هذا المُنشئ تمرير إعدادات قادمة من مصادر بيانات متعددة مثل
        ملفات YAML أو متغيرات بيئة محوّلة مسبقاً إلى أزواج مرتّبة.
        """

        return cls(_config=dict(items))

    def get(self, key: str, default: ConfigValue | None = None) -> ConfigValue | None:
        """إرجاع قيمة الإعداد المطلوب مع دعم قيمة افتراضية واضحة.

        Args:
            key: اسم المفتاح المطلوب.
            default: القيمة المعادة عند غياب المفتاح.
        """

        return self._config.get(key, default)

    def set(self, key: str, value: ConfigValue) -> None:
        """تحديث أو إضافة قيمة إعداد محددة.

        Args:
            key: اسم المفتاح المراد ضبطه.
            value: القيمة الجديدة المتوافقة مع نوع الإعدادات.
        """

        self._config[key] = value

    def to_dict(self) -> dict[str, ConfigValue]:
        """إرجاع نسخة مستقلة من الإعدادات الحالية.

        تعيد هذه الدالة نسخة سطحية لتجنّب تعديل القيم الداخلية بدون قصد.
        """

        return dict(self._config)
