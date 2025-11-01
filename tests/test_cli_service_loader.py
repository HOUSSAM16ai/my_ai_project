# tests/test_cli_service_loader.py
# ======================================================================================
# TESTS FOR SERVICE LOADER - SRP REFACTORING
# ======================================================================================
"""
اختبارات للتحقق من أن ServiceLoader يعمل بشكل صحيح ويحترم مبدأ المسؤولية الواحدة.
"""

import pytest

from app.cli.service_loader import (
    DatabaseBinder,
    ImportRecord,
    ModuleImporter,
    ServiceBinder,
    ServiceLoader,
    get_loader,
    reset_loader,
)


class TestImportRecord:
    """اختبارات لـ ImportRecord"""

    def test_import_record_initialization(self):
        """التحقق من إنشاء سجل استيراد جديد"""
        rec = ImportRecord("test.module")
        assert rec.name == "test.module"
        assert rec.ok is False
        assert rec.error is None
        assert rec.trace is None
        assert rec.module is None

    def test_import_record_to_dict(self):
        """التحقق من تحويل السجل إلى قاموس"""
        rec = ImportRecord("test.module")
        rec.ok = True
        data = rec.to_dict()
        assert data["name"] == "test.module"
        assert data["ok"] is True
        assert data["error"] is None
        assert "trace" in data


class TestModuleImporter:
    """اختبارات لـ ModuleImporter"""

    def test_module_importer_initialization(self):
        """التحقق من إنشاء مستورد وحدات جديد"""
        importer = ModuleImporter()
        assert isinstance(importer.imports, dict)
        assert len(importer.imports) == 0

    def test_import_valid_module(self):
        """التحقق من استيراد وحدة صالحة"""
        importer = ModuleImporter()
        rec = importer.import_module("json")
        assert rec.ok is True
        assert rec.error is None
        assert rec.module is not None

    def test_import_invalid_module(self):
        """التحقق من التعامل مع وحدة غير موجودة"""
        importer = ModuleImporter()
        rec = importer.import_module("nonexistent_module_12345")
        assert rec.ok is False
        assert rec.error is not None
        assert rec.trace is not None

    def test_import_modules_list(self):
        """التحقق من استيراد قائمة وحدات"""
        importer = ModuleImporter()
        records = importer.import_modules(["json", "os", "sys"])
        assert len(records) == 3
        assert all(r.ok for r in records)

    def test_get_record(self):
        """التحقق من الحصول على سجل وحدة"""
        importer = ModuleImporter()
        importer.import_module("json")
        rec = importer.get_record("json")
        assert rec is not None
        assert rec.ok is True

    def test_has_failures(self):
        """التحقق من اكتشاف الفشل في الوحدات"""
        importer = ModuleImporter()
        importer.import_module("json")
        importer.import_module("nonexistent_module")

        assert importer.has_failures(["json"]) is False
        assert importer.has_failures(["nonexistent_module"]) is True

    def test_get_failed_modules(self):
        """التحقق من الحصول على الوحدات الفاشلة"""
        importer = ModuleImporter()
        importer.import_module("json")
        importer.import_module("nonexistent_module")

        failed = importer.get_failed_modules()
        assert len(failed) >= 1
        assert any(not r.ok for r in failed)


class TestDatabaseBinder:
    """اختبارات لـ DatabaseBinder"""

    def test_database_binder_initialization(self):
        """التحقق من إنشاء ربط قاعدة البيانات"""
        importer = ModuleImporter()
        binder = DatabaseBinder(importer)
        assert binder.importer is importer
        assert binder.is_ready is False
        assert binder.db is None

    def test_get_models_dict(self):
        """التحقق من الحصول على قاموس النماذج"""
        importer = ModuleImporter()
        binder = DatabaseBinder(importer)
        models = binder.get_models()

        assert isinstance(models, dict)
        assert "db" in models
        assert "User" in models
        assert "Mission" in models


class TestServiceBinder:
    """اختبارات لـ ServiceBinder"""

    def test_service_binder_initialization(self):
        """التحقق من إنشاء ربط الخدمات"""
        importer = ModuleImporter()
        binder = ServiceBinder(importer)
        assert binder.importer is importer
        assert binder.is_ready is False
        assert binder.generation_service is None

    def test_get_services_dict(self):
        """التحقق من الحصول على قاموس الخدمات"""
        importer = ModuleImporter()
        binder = ServiceBinder(importer)
        services = binder.get_services()

        assert isinstance(services, dict)
        assert "generation_service" in services
        assert "system_service" in services
        assert "agent_tools" in services
        assert "overmind" in services


class TestServiceLoader:
    """اختبارات لـ ServiceLoader"""

    def test_service_loader_initialization(self):
        """التحقق من إنشاء محمل الخدمات"""
        loader = ServiceLoader()
        assert isinstance(loader.importer, ModuleImporter)
        assert isinstance(loader.db_binder, DatabaseBinder)
        assert isinstance(loader.service_binder, ServiceBinder)
        assert loader._loaded is False

    def test_module_lists_defined(self):
        """التحقق من تعريف قوائم الوحدات"""
        loader = ServiceLoader()
        assert len(loader.DB_MODULES) > 0
        assert len(loader.SERVICE_MODULES) > 0
        assert len(loader.PLANNING_MODULES) > 0

    def test_get_all_imports(self):
        """التحقق من الحصول على جميع سجلات الاستيراد"""
        loader = ServiceLoader()
        imports = loader.get_all_imports()
        assert isinstance(imports, dict)

    def test_singleton_loader(self):
        """التحقق من نمط Singleton للمحمل"""
        reset_loader()  # إعادة تعيين للتأكد من البداية النظيفة

        loader1 = get_loader()
        loader2 = get_loader()
        assert loader1 is loader2  # نفس النسخة

        reset_loader()  # تنظيف بعد الاختبار


class TestSRPCompliance:
    """اختبارات للتحقق من الالتزام بمبدأ المسؤولية الواحدة"""

    def test_module_importer_single_responsibility(self):
        """التحقق من أن ModuleImporter مسؤول فقط عن الاستيراد"""
        importer = ModuleImporter()

        # يجب أن يكون له وظائف استيراد فقط
        assert hasattr(importer, "import_module")
        assert hasattr(importer, "import_modules")
        assert hasattr(importer, "get_record")

        # لا يجب أن يحتوي على منطق ربط
        assert not hasattr(importer, "bind")
        assert not hasattr(importer, "bind_services")

    def test_database_binder_single_responsibility(self):
        """التحقق من أن DatabaseBinder مسؤول فقط عن ربط قاعدة البيانات"""
        importer = ModuleImporter()
        binder = DatabaseBinder(importer)

        # يجب أن يكون له وظائف ربط قاعدة البيانات فقط
        assert hasattr(binder, "bind")
        assert hasattr(binder, "get_models")

        # لا يجب أن يحتوي على منطق استيراد
        assert not hasattr(binder, "import_module")
        assert not hasattr(binder, "import_modules")

    def test_service_binder_single_responsibility(self):
        """التحقق من أن ServiceBinder مسؤول فقط عن ربط الخدمات"""
        importer = ModuleImporter()
        binder = ServiceBinder(importer)

        # يجب أن يكون له وظائف ربط الخدمات فقط
        assert hasattr(binder, "bind")
        assert hasattr(binder, "get_services")

        # لا يجب أن يحتوي على منطق استيراد أو ربط قاعدة البيانات
        assert not hasattr(binder, "import_module")
        assert not hasattr(binder, "get_models")

    def test_service_loader_coordinates_not_implements(self):
        """التحقق من أن ServiceLoader ينسق فقط ولا ينفذ التفاصيل"""
        loader = ServiceLoader()

        # يجب أن يستخدم المكونات المتخصصة
        assert hasattr(loader, "importer")
        assert hasattr(loader, "db_binder")
        assert hasattr(loader, "service_binder")

        # يجب أن يكون له وظيفة تنسيق رئيسية
        assert hasattr(loader, "load")

        # يجب أن يفوض المهام للمكونات المتخصصة
        assert isinstance(loader.importer, ModuleImporter)
        assert isinstance(loader.db_binder, DatabaseBinder)
        assert isinstance(loader.service_binder, ServiceBinder)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
