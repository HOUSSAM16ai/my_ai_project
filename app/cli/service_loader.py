# app/cli/service_loader.py
# ======================================================================================
# SERVICE LOADER - SINGLE RESPONSIBILITY REFACTORING
# ======================================================================================
# PURPOSE:
#   فصل مسؤوليات تحميل الخدمات إلى مكونات متخصصة:
#     - ModuleImporter: استيراد الوحدات وتتبع الأخطاء
#     - DatabaseBinder: ربط نماذج قاعدة البيانات
#     - ServiceBinder: ربط الخدمات
#     - ServiceLoader: تنسيق العملية الكاملة
#
# BENEFITS:
#   - كل class له مسؤولية واحدة واضحة
#   - سهولة الاختبار والصيانة
#   - إمكانية إعادة الاستخدام
#   - أكثر قابلية للتوسع
# ======================================================================================
from __future__ import annotations

import importlib
import traceback
from types import ModuleType
from typing import Any, Optional


# ======================================================================================
# IMPORT RECORD - تتبع حالة استيراد الوحدات
# ======================================================================================
class ImportRecord:
    """سجل لتتبع نجاح أو فشل استيراد وحدة معينة"""
    
    def __init__(self, name: str):
        self.name = name
        self.ok = False
        self.error: Optional[BaseException] = None
        self.trace: Optional[str] = None
        self.module: Optional[ModuleType] = None

    def to_dict(self, include_trace: bool = False) -> dict[str, Any]:
        """تحويل السجل إلى قاموس للعرض أو التصدير"""
        return {
            "name": self.name,
            "ok": self.ok,
            "error": repr(self.error) if self.error else None,
            "trace": self.trace if include_trace else None,
        }


# ======================================================================================
# MODULE IMPORTER - مسؤول عن استيراد الوحدات فقط
# ======================================================================================
class ModuleImporter:
    """مسؤول عن استيراد الوحدات وتتبع النجاح/الفشل"""
    
    def __init__(self):
        self.imports: dict[str, ImportRecord] = {}
    
    def import_module(self, path: str) -> ImportRecord:
        """استيراد وحدة واحدة وتسجيل النتيجة"""
        if path in self.imports:
            return self.imports[path]
        
        rec = ImportRecord(path)
        try:
            rec.module = importlib.import_module(path)
            rec.ok = True
        except Exception as e:
            rec.error = e
            rec.trace = traceback.format_exc()
        
        self.imports[path] = rec
        return rec
    
    def import_modules(self, paths: list[str]) -> list[ImportRecord]:
        """استيراد قائمة من الوحدات"""
        return [self.import_module(path) for path in paths]
    
    def get_record(self, path: str) -> Optional[ImportRecord]:
        """الحصول على سجل استيراد وحدة"""
        return self.imports.get(path)
    
    def has_failures(self, paths: list[str]) -> bool:
        """التحقق من وجود فشل في قائمة وحدات محددة"""
        return any(
            rec.name in paths and not rec.ok
            for rec in self.imports.values()
        )
    
    def get_failed_modules(self, paths: list[str] = None) -> list[ImportRecord]:
        """الحصول على قائمة الوحدات الفاشلة"""
        if paths:
            return [
                rec for rec in self.imports.values()
                if rec.name in paths and not rec.ok
            ]
        return [rec for rec in self.imports.values() if not rec.ok]


# ======================================================================================
# DATABASE BINDER - مسؤول عن ربط نماذج قاعدة البيانات
# ======================================================================================
class DatabaseBinder:
    """مسؤول عن ربط نماذج قاعدة البيانات بعد الاستيراد الناجح"""
    
    def __init__(self, importer: ModuleImporter):
        self.importer = importer
        self.db = None
        self.User = None
        self.Mission = None
        self.MissionPlan = None
        self.Task = None
        self.MissionStatus = None
        self.TaskStatus = None
        self.is_ready = False
    
    def bind(self) -> bool:
        """ربط جميع نماذج قاعدة البيانات"""
        models_rec = self.importer.get_record("app.models")
        if not models_rec or not models_rec.ok:
            return False
        
        try:
            from app import db as _db
            from app.models import (
                Mission as _Mission,
                MissionPlan as _MissionPlan,
                MissionStatus as _MissionStatus,
                Task as _Task,
                TaskStatus as _TaskStatus,
                User as _User,
            )
            
            self.db = _db
            self.User = _User
            self.Mission = _Mission
            self.MissionPlan = _MissionPlan
            self.Task = _Task
            self.MissionStatus = _MissionStatus
            self.TaskStatus = _TaskStatus
            self.is_ready = True
            return True
            
        except Exception as e:
            # تسجيل الخطأ في سجل الاستيراد
            models_rec.ok = False
            models_rec.error = e
            models_rec.trace = traceback.format_exc()
            self.is_ready = False
            return False
    
    def get_models(self) -> dict[str, Any]:
        """الحصول على جميع النماذج المربوطة"""
        return {
            "db": self.db,
            "User": self.User,
            "Mission": self.Mission,
            "MissionPlan": self.MissionPlan,
            "Task": self.Task,
            "MissionStatus": self.MissionStatus,
            "TaskStatus": self.TaskStatus,
        }


# ======================================================================================
# SERVICE BINDER - مسؤول عن ربط الخدمات
# ======================================================================================
class ServiceBinder:
    """مسؤول عن ربط الخدمات والتخطيط بعد الاستيراد الناجح"""
    
    def __init__(self, importer: ModuleImporter):
        self.importer = importer
        self.generation_service = None
        self.system_service = None
        self.agent_tools = None
        self.overmind = None
        self.planning = None
        self.MissionPlanSchema = None
        self.PlanWarning = None
        self.is_ready = False
    
    def bind(self) -> bool:
        """ربط جميع الخدمات"""
        try:
            # ربط خدمات التوليد
            if self._is_module_ok("app.services.generation_service"):
                import app.services.generation_service as _gen
                self.generation_service = _gen
            
            # ربط خدمات النظام
            if self._is_module_ok("app.services.system_service"):
                import app.services.system_service as _sys
                self.system_service = _sys
            
            # ربط أدوات العميل
            if self._is_module_ok("app.services.agent_tools"):
                import app.services.agent_tools as _tools
                self.agent_tools = _tools
            
            # ربط Overmind
            if self._is_module_ok("app.services.master_agent_service"):
                import app.services.master_agent_service as _over
                self.overmind = _over
            
            # ربط مخططات التخطيط
            if self._is_module_ok("app.overmind.planning.schemas"):
                from app.overmind.planning.schemas import (
                    MissionPlanSchema as _MPS,
                    PlanWarning as _PW,
                )
                self.MissionPlanSchema = _MPS
                self.PlanWarning = _PW
            
            # ربط مصنع التخطيط
            if self._is_module_ok("app.overmind.planning.factory"):
                import app.overmind.planning.factory as _planning_factory
                self.planning = _planning_factory
            
            self.is_ready = True
            return True
            
        except Exception as e:
            # تسجيل خطأ في مرحلة الربط
            rec = ImportRecord("binding-phase")
            rec.error = e
            rec.trace = traceback.format_exc()
            self.importer.imports["binding-phase"] = rec
            self.is_ready = False
            return False
    
    def _is_module_ok(self, module_path: str) -> bool:
        """التحقق من نجاح استيراد وحدة معينة"""
        rec = self.importer.get_record(module_path)
        return rec is not None and rec.ok
    
    def get_services(self) -> dict[str, Any]:
        """الحصول على جميع الخدمات المربوطة"""
        return {
            "generation_service": self.generation_service,
            "system_service": self.system_service,
            "agent_tools": self.agent_tools,
            "overmind": self.overmind,
            "planning": self.planning,
            "MissionPlanSchema": self.MissionPlanSchema,
            "PlanWarning": self.PlanWarning,
        }


# ======================================================================================
# SERVICE LOADER - ينسق عملية التحميل الكاملة
# ======================================================================================
class ServiceLoader:
    """منسق رئيسي يدير عملية تحميل جميع الخدمات والنماذج"""
    
    # قوائم الوحدات المطلوبة
    DB_MODULES = [
        "app",
        "app.models",
    ]
    
    SERVICE_MODULES = [
        "app.services.generation_service",
        "app.services.system_service",
        "app.services.agent_tools",
        "app.services.master_agent_service",
    ]
    
    PLANNING_MODULES = [
        "app.overmind.planning.schemas",
        "app.overmind.planning.factory",
        "app.overmind.planning.llm_planner",
    ]
    
    def __init__(self, relax_imports: bool = False):
        self.relax_imports = relax_imports
        self.importer = ModuleImporter()
        self.db_binder = DatabaseBinder(self.importer)
        self.service_binder = ServiceBinder(self.importer)
        self._loaded = False
    
    def load(self, force: bool = False) -> bool:
        """تحميل جميع الخدمات والنماذج"""
        if self._loaded and not force:
            return self.is_ready()
        
        # 1. استيراد وحدات قاعدة البيانات
        self.importer.import_modules(self.DB_MODULES)
        
        # 2. ربط نماذج قاعدة البيانات
        self.db_binder.bind()
        
        # 3. استيراد وحدات الخدمات والتخطيط
        self.importer.import_modules(self.SERVICE_MODULES)
        self.importer.import_modules(self.PLANNING_MODULES)
        
        # 4. التحقق من الفشل الحرج
        if self._has_critical_failures() and not self.relax_imports:
            self._loaded = True
            return False
        
        # 5. ربط الخدمات
        self.service_binder.bind()
        
        self._loaded = True
        return self.is_ready()
    
    def _has_critical_failures(self) -> bool:
        """التحقق من وجود فشل في الوحدات الحرجة"""
        critical_modules = self.SERVICE_MODULES + self.PLANNING_MODULES
        return self.importer.has_failures(critical_modules)
    
    def is_ready(self) -> bool:
        """التحقق من جاهزية جميع الخدمات"""
        return self.service_binder.is_ready
    
    def is_db_ready(self) -> bool:
        """التحقق من جاهزية قاعدة البيانات"""
        return self.db_binder.is_ready
    
    def get_all_imports(self) -> dict[str, ImportRecord]:
        """الحصول على جميع سجلات الاستيراد"""
        return self.importer.imports
    
    def get_failed_modules(self) -> list[ImportRecord]:
        """الحصول على قائمة الوحدات الفاشلة"""
        return self.importer.get_failed_modules()
    
    def get_db_models(self) -> dict[str, Any]:
        """الحصول على نماذج قاعدة البيانات"""
        return self.db_binder.get_models()
    
    def get_services(self) -> dict[str, Any]:
        """الحصول على الخدمات"""
        return self.service_binder.get_services()


# ======================================================================================
# SINGLETON INSTANCE - نسخة واحدة مشتركة
# ======================================================================================
_loader_instance: Optional[ServiceLoader] = None


def get_loader(relax_imports: bool = False) -> ServiceLoader:
    """الحصول على نسخة ServiceLoader المشتركة"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ServiceLoader(relax_imports=relax_imports)
    return _loader_instance


def reset_loader():
    """إعادة تعيين النسخة المشتركة (للاختبار)"""
    global _loader_instance
    _loader_instance = None
