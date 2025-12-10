"""
Model Registry
==============
Manages the lifecycle of AI model versions.
Responsible for registration, loading, unloading, and status management.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime

from app.serving.domain.entities import ModelStatus, ModelVersion


class ModelRegistry:
    """
    Model Registry - إدارة دورة حياة النماذج
    
    Responsibilities:
    - Register new model versions
    - Load and unload models
    - Track model status
    - Manage model lifecycle
    """

    def __init__(self):
        self._models: dict[str, ModelVersion] = {}
        self._lock = threading.RLock()

    def register_model(self, model: ModelVersion) -> bool:
        """
        تسجيل نموذج جديد
        
        Args:
            model: نسخة النموذج
            
        Returns:
            نجاح التسجيل
        """
        with self._lock:
            if model.version_id in self._models:
                return False

            model.status = ModelStatus.LOADING
            self._models[model.version_id] = model

            # محاكاة تحميل النموذج
            def load_model():
                time.sleep(2)  # محاكاة وقت التحميل
                with self._lock:
                    model.status = ModelStatus.READY
                    model.loaded_at = datetime.now(UTC)

            threading.Thread(target=load_model, daemon=True).start()

            return True

    def unload_model(self, version_id: str) -> bool:
        """
        إلغاء تحميل نموذج
        
        Args:
            version_id: معرف النسخة
            
        Returns:
            نجاح الإلغاء
        """
        with self._lock:
            if version_id not in self._models:
                return False

            model = self._models[version_id]
            model.status = ModelStatus.DRAINING

            # انتظار انتهاء الطلبات الحالية
            def drain_and_stop():
                time.sleep(5)
                with self._lock:
                    model.status = ModelStatus.STOPPED

            threading.Thread(target=drain_and_stop, daemon=True).start()

            return True

    def get_model(self, version_id: str) -> ModelVersion | None:
        """Get model by version ID"""
        with self._lock:
            return self._models.get(version_id)

    def get_latest_ready_model(self, model_name: str) -> ModelVersion | None:
        """
        الحصول على أحدث نسخة جاهزة من النموذج
        
        Args:
            model_name: اسم النموذج
            
        Returns:
            أحدث نسخة جاهزة أو None
        """
        with self._lock:
            candidates = [
                m for m in self._models.values()
                if m.model_name == model_name and m.status == ModelStatus.READY
            ]

            if not candidates:
                return None

            # ترتيب حسب تاريخ الإنشاء
            candidates.sort(key=lambda m: m.created_at, reverse=True)
            return candidates[0]

    def list_models(self) -> list[ModelVersion]:
        """
        قائمة بكل النماذج المسجلة
        
        Returns:
            قائمة النماذج
        """
        with self._lock:
            return list(self._models.values())

    def get_model_status(self, version_id: str) -> ModelVersion | None:
        """
        الحصول على حالة النموذج
        
        Args:
            version_id: معرف النسخة
            
        Returns:
            النموذج أو None
        """
        return self.get_model(version_id)
